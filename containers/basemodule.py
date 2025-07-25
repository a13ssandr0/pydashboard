import inspect
import traceback
from functools import wraps
from re import sub
from threading import Event
from time import sleep
from typing import Literal

from durations import Duration
from loguru import logger
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.css._style_properties import (BorderProperty, ColorProperty,
                                           StyleFlagsProperty)
from textual.css.types import AlignHorizontal, AlignVertical
from textual.widgets import Static

from utils.ssh import SSHManager
from utils.types import Size

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

    def __init__(self, *,
                 id: str = None,
                 mod_type: str = None,
                 refreshInterval: Literal['never'] | int | float | str = None,
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
                 **kwargs):
        """Init module and load config"""
        id = sub(r"[^\w\d\-_]", "_", id)
        if id[0].isdigit(): id = "_" + id

        super().__init__(id=id)

        if isinstance(refreshInterval, str) and refreshInterval != 'never':
            refreshInterval = Duration(refreshInterval).to_seconds()
        self.refreshInterval = refreshInterval
        logger.info('Setting {} refresh interval to {} second(s)', id, refreshInterval)

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
            'refreshInterval'                  : refreshInterval,
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

        if remote_host:
            self.remote_root, self.sess_id = SSHManager.create_session(host=remote_host, port=remote_port,
                                                                       user=remote_username,
                                                                       password=remote_password, keyfile=remote_key)

            self.remote_root.init_module(module_name=mod_type, _id=id, refreshInterval=refreshInterval,
                                         align_horizontal=align_horizontal, align_vertical=align_vertical,
                                         color=color, border=border, title=title, title_align=title_align,
                                         title_background=title_background, title_color=title_color,
                                         title_style=title_style, subtitle=subtitle,
                                         subtitle_align=subtitle_align, subtitle_background=subtitle_background,
                                         subtitle_color=subtitle_color, subtitle_style=subtitle_style,
                                         **kwargs)

            self.call_target = self.remote_root.call_module
            self.post_init_target = self.remote_root.post_init_module
        else:
            self.call_target = self.__call__
            self.post_init_target = self.__post_init__

    def __del__(self):
        if self.remote_root:
            SSHManager.close_session(self.sess_id)
            self.remote_root = None
            self.sess_id = None

    def reset_settings(self, key):
        value = self.__user_settings.get(key)
        if value is not None:
            match key:
                case 'refreshInterval':
                    self.refreshInterval = value
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

        if self.remote_root:
            return func(self.id, *args, **kwargs)
        else:
            return func(*args, **kwargs)

    def update(self, *args, **kwargs):
        result = self.inject_dependencies(self.call_target, *args, reference_func=self.__call__, **kwargs)
        if result is not None:
            self.inner.update(result)

    def _update(self):
        try:
            self.update()
        except Exception as e:
            super().notify(traceback.format_exc(), severity='error')
            logger.exception(str(e))

    def on_ready(self, signal: Event):
        try:
            self.inject_dependencies(self.post_init_target, reference_func=self.__post_init__)
        except Exception as e:
            super().notify(traceback.format_exc(), severity='error')
            logger.exception(str(e))
        if self.refreshInterval == 'never':
            self._update()
            return
        while not signal.is_set():
            self._update()
            for _ in range(round(self.refreshInterval)):
                if signal.is_set(): return
                sleep(1)

    def notify(self, message, *, title="", severity="information", timeout=None, **kwargs):
        logger.log(severity_map.get(severity, "INFO"), message)
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
    def __init__(self, content="", **kwargs):
        super().__init__(content, **kwargs)
        logger.error(content)

    def compose(self):
        self.border_title = "Module error"
        yield from super().compose()
