import inspect
import traceback
from functools import wraps
from random import randint
from re import sub
from threading import Event
from time import sleep
from typing import Any, Literal

from durations import Duration
from loguru import logger
from plumbum.machines.session import HostPublicKeyUnknown, IncorrectLogin, SSHCommsChannel2Error, SSHCommsError
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.css._style_properties import BorderProperty, ColorProperty, StyleFlagsProperty
from textual.css.types import AlignHorizontal, AlignVertical
from textual.widgets import Static

from pydashboard.utils.ssh import SessionManager
from pydashboard.utils.types import Size

severity_map = {
    'information': "INFO",
    'warning'    : "WARNING",
    'error'      : "ERROR"
}


# noinspection PyPep8Naming,PyShadowingBuiltins
class BaseModule(ScrollableContainer):
    inner = Static
    remote_root = None
    sess_id = None
    conn_id = None
    remote_settings = None

    def __init__(self, *,
                 id: str = None,
                 mod_type: str = None,
                 refresh_interval: Literal['never'] | int | float | str = None,
                 align_horizontal: AlignHorizontal = "left",
                 align_vertical: AlignVertical = "top",
                 color: ColorProperty = None,
                 border: BorderProperty | tuple = ("round", "white"),
                 title: str = None,
                 title_align: AlignHorizontal = "center",
                 title_background: ColorProperty = None,
                 title_color: ColorProperty = "white",
                 title_style: StyleFlagsProperty = None,
                 subtitle: str = None,
                 subtitle_align: AlignHorizontal = "right",
                 subtitle_background: ColorProperty = None,
                 subtitle_color: ColorProperty = "white",
                 subtitle_style: StyleFlagsProperty = None,
                 remote_host: str = None,
                 remote_port: int = None,
                 remote_username: str = None,
                 remote_password: str = None,
                 remote_key: str = None,
                 ssh_strict_host_key_checking: Literal[None, True, False, 'accept-new'] = None,
                 # man ssh_config(5) - StrictHostKeyChecking
                 ssh_ignore_known_hosts_file: bool = False,
                 **kwargs: Any):
        """

        Args:
            refresh_interval: How often to update module data, accepts a value in seconds or string with a time unit.
                                'never' disables updating
            align_horizontal: Horizontal alignment of the text
            align_vertical: Vertical alignment of the text
            color: Color of the text
            border: Border of the widget
            title: Title of the widget
            title_align: Alignment of the title
            title_background: Background color of the title
            title_color: Color of the title
            title_style: Style of the title
            subtitle: Title of the subwidget
            subtitle_align: Alignment of the subtitle
            subtitle_background: Background color of the subtitle
            subtitle_color: Color of the subtitle
            subtitle_style: Style of the subtitle
            remote_host: Remote host IP or FQDN
            remote_port: Remote host SSH port
            remote_username: Remote host SSH username
            remote_password: Remote host SSH password
            remote_key: Remote host SSH key
            ssh_strict_host_key_checking: Control host key verification behaviour
            ssh_ignore_known_hosts_file: Ignore known hosts file (suppresses host key changed warning)
        """
        id = sub(r"[^\w\d\-_]", "_", id)
        if id[0].isdigit(): id = "_" + id

        super().__init__(id=id)

        self.logger = logger.bind(module=f"{self.__class__.__name__}(id={id})")
        # noinspection PyTypeChecker
        self.on_ready = self.logger.catch()(self.on_ready)

        if isinstance(refresh_interval, str) and refresh_interval != 'never':
            refresh_interval = Duration(refresh_interval).to_seconds()
        self.refresh_interval = refresh_interval
        self.logger.info('Setting {} refresh interval to {} second(s)', id, refresh_interval)

        self.styles.align_horizontal = align_horizontal
        self.styles.align_vertical = align_vertical

        self.styles.color = color

        self.styles.border = tuple(border) if border else ("none", "black")
        self.border_title = title if title is not None else self.__class__.__name__
        self.styles.border_title_align = title_align
        self.styles.border_title_background = title_background
        self.styles.border_title_color = title_color
        self.styles.border_title_style = title_style
        self.border_subtitle = subtitle
        self.styles.border_subtitle_align = subtitle_align
        self.styles.border_subtitle_background = subtitle_background
        self.styles.border_subtitle_color = subtitle_color
        self.styles.border_subtitle_style = subtitle_style

        self.__user_settings = {
            'refresh_interval'                  : refresh_interval,
            'styles.align_horizontal'          : align_horizontal,
            'styles.align_vertical'            : align_vertical,
            'styles.color'                     : color,
            'styles.border'                    : tuple(border) if border else "none",
            'border_title'                     : title if title is not None else self.__class__.__name__,
            'styles.border_title_align'        : title_align,
            'styles.border_title_background'   : title_background,
            'styles.border_title_color'        : title_color,
            'styles.border_title_style'        : title_style,
            'border_subtitle'                  : subtitle,
            'styles.border_subtitle_align'     : subtitle_align,
            'styles.border_subtitle_background': subtitle_background,
            'styles.border_subtitle_color'     : subtitle_color,
            'styles.border_subtitle_style'     : subtitle_style,
        }

        self.inner = self.inner()
        self.inner.styles.width = "auto"
        self.inner.styles.height = "auto"

        self.call_target = self.__call__
        self.post_init_target = self.__post_init__

        if remote_host and '@' in remote_host:
            self.remote_host, self.remote_username = remote_host.split('@', 1)
        else:
            self.remote_host = remote_host
        self.remote_port = remote_port
        self.remote_username = remote_username
        self.remote_password = remote_password
        self.remote_key = remote_key
        self.mod_type = mod_type
        self.ssh_strict_host_key_checking = ssh_strict_host_key_checking
        self.ssh_ignore_known_hosts_file = ssh_ignore_known_hosts_file

        if remote_host:
            self.prepare_remote(remote_host, remote_port, remote_username, remote_password, remote_key, mod_type,
                                ssh_strict_host_key_checking, ssh_ignore_known_hosts_file,
                                id=id, refresh_interval=refresh_interval,
                                align_horizontal=align_horizontal, align_vertical=align_vertical,
                                color=color, border=border, title=title, title_align=title_align,
                                title_background=title_background, title_color=title_color,
                                title_style=title_style, subtitle=subtitle,
                                subtitle_align=subtitle_align, subtitle_background=subtitle_background,
                                subtitle_color=subtitle_color, subtitle_style=subtitle_style,
                                **kwargs)

    def prepare_remote(self, remote_host, remote_port, remote_username, remote_password, remote_key, mod_type,
                       ssh_strict_host_key_checking, ssh_ignore_known_hosts_file, **kwargs):
        self.remote_settings = {
            'connection': {
                'host'                        : remote_host,
                'port'                        : remote_port,
                'user'                        : remote_username,
                'password'                    : remote_password,
                'keyfile'                     : remote_key,
                'ssh_strict_host_key_checking': ssh_strict_host_key_checking,
                'ssh_ignore_known_hosts_file' : ssh_ignore_known_hosts_file
            },
            'session'   : {
                'module_name'    : mod_type,
                'setter_function': self.set
            },
            'kwargs'    : kwargs,
        }

    def init_remote(self):
        self.conn_id = SessionManager.create_connection(**self.remote_settings['connection'])

        self.remote_root, self.sess_id = SessionManager.create_session(self.conn_id, **self.remote_settings['session'])

        self.remote_root.init_module(**self.remote_settings['kwargs'])

        self.call_target = self.remote_root.call_module
        self.post_init_target = self.remote_root.post_init_module

    def __del__(self):
        if self.remote_root:
            SessionManager.close(sess_id=self.sess_id)
            self.remote_root = None
            self.sess_id = None
            self.conn_id = None

    def set(self, key, value):
        match key:
            case 'refresh_interval':
                self.refresh_interval = value
            case 'styles.align_horizontal':
                self.styles.align_horizontal = value
            case 'styles.align_vertical':
                self.styles.align_vertical = value
            case 'styles.color':
                self.styles.color = value
            case 'styles.border':
                self.styles.border = value
            case 'border_title':
                self.border_title = value
            case 'styles.border_title_align':
                self.styles.border_title_align = value
            case 'styles.border_title_background':
                self.styles.border_title_background = value
            case 'styles.border_title_color':
                self.styles.border_title_color = value
            case 'styles.border_title_style':
                self.styles.border_title_style = value
            case 'border_subtitle':
                self.border_subtitle = value
            case 'styles.border_subtitle_align':
                self.styles.border_subtitle_align = value
            case 'styles.border_subtitle_background':
                self.styles.border_subtitle_background = value
            case 'styles.border_subtitle_color':
                self.styles.border_subtitle_color = value
            case 'styles.border_subtitle_style':
                self.styles.border_subtitle_style = value

    def reset_settings(self, key):
        try:
            self.set(key, self.__user_settings[key])
        except KeyError:
            pass

    def reload_styles(self):
        for k, v in self.__user_settings.items():
            self.set(k, v)

    def __post_init__(self, *args, **kwargs):
        """Perform post initialization tasks"""
        pass

    def __call__(self, *args, **kwargs) -> str | Text:
        """Method called each time the module has to be updated"""
        pass

    def inject_dependencies(self, func, *args, reference_func=None, **kwargs):
        # Inspect function signature to check if it has a Size parameter
        signature = inspect.signature(reference_func or func)

        coord_param = None
        for param_name, param in signature.parameters.items():
            if param.annotation is Size and coord_param is None:
                coord_param = param_name

        if coord_param:
            kwargs[coord_param] = (
                self.content_size.height,
                self.content_size.width,
            )

        return func(*args, **kwargs)

    def update(self, *args, **kwargs):
        result = self.inject_dependencies(self.call_target, *args, reference_func=self.__call__, **kwargs)
        if result is not None:
            self.inner.update(result)

    def on_ready(self, signal: Event):
        while not signal.is_set():
            try:
                if self.remote_settings:
                    self.init_remote()
                self.reload_styles()
                self.inject_dependencies(self.post_init_target, reference_func=self.__post_init__)

                if self.refresh_interval == 'never':
                    self.update()
                    return

                while not signal.is_set():
                    self.update()
                    self.interruptibleWait(self.refresh_interval, signal)

            except SSHCommsChannel2Error as e:
                self.handle_remote_connection_exception("SSH: stderr not available", e, signal)
            except IncorrectLogin as e:
                self.handle_remote_connection_exception("SSH: incorrect login", e, signal)
            except HostPublicKeyUnknown as e:
                self.handle_remote_connection_exception("SSH: unknown host public key", e, signal)

            except SSHCommsError as e:
                ## ssh to a nonexistent/offline host
                self.handle_remote_connection_exception("SSH: " + e.stderr.split(':')[-1].strip(), e, signal)
            except (
                    ConnectionRefusedError, ConnectionResetError,  ## local port not available
                    EOFError  ## nothing listening on the remote side of the tunnel
            ) as e:
                if self.conn_id:
                    SessionManager.close(conn_id=self.conn_id)
                self.handle_remote_connection_exception(
                        f"{self.remote_host} not listening for connections, closing connection \"{self.conn_id}\"", e,
                        signal)

            except Exception as e:
                super().notify(traceback.format_exc(), severity='error')
                self.logger.exception(str(e))
                self.interruptibleWait(self.refresh_interval if self.refresh_interval != 'never' else 30, signal)

    def handle_remote_connection_exception(self, text, e, signal):
        self.styles.border = ("round", "red")
        self.styles.border_subtitle_color = "red"
        self.border_subtitle = text
        super().notify(f"[red]{text}[/red].\n{e}", severity='error')
        self.logger.opt(depth=1).critical(f"{text} - {e}")
        self.interruptibleWait(randint(10, 20), signal)

    @staticmethod
    def interruptibleWait(seconds, signal):
        for _ in range(round(seconds)):
            if signal.is_set(): return
            sleep(1)

    def notify(self, message, *, title="", severity="information", timeout=None, **kwargs):
        self.logger.opt(depth=1).log(severity_map.get(severity, "INFO"), message)
        return super().notify(message, title=title, severity=severity, timeout=timeout)

    def compose(self):
        yield self.inner


class ErrorModule(Static):
    DEFAULT_CSS = """
        ErrorModule {
            border: heavy red;
            border-title-align: center;
            border-title-color: red;
            color: red;
        }
    """

    @wraps(Static.__init__)
    def __init__(self, content="", markup=False,  **kwargs):
        super().__init__(content, markup=markup, **kwargs)
        logger.error(content)

    def compose(self):
        self.border_title = "Module error"
        yield from super().compose()
