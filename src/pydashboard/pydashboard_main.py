import os
import re
import sys
from argparse import ArgumentParser, BooleanOptionalAction
from importlib import import_module
from pathlib import Path
from threading import Event, Thread
from typing import Any, Type, cast

from benedict import benedict
from benedict.core import rename
from benedict.utils import type_util
from loguru import logger
from textual._path import CSSPathType
from textual.app import App
from textual.binding import Binding
from textual.driver import Driver
from watchfiles import watch

# noinspection PyUnboundLocalVariable
if not __package__:
    # Make CLI runnable from source tree with python src/package
    __package__ = os.path.basename(os.path.dirname(__file__))
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)

from .containers import BaseModule, ErrorModule, GenericModule as Module
from .utils.ssh import SessionManager
from .utils.types import Coordinates


class MainApp(App):
    CSS = r"""Screen {overflow: hidden hidden;}"""
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False, priority=True)]
    signal = Event()
    config: dict
    ready_hooks = {}
    modules_threads = []

    def __init__(self, config: dict, driver_class: Type[Driver] | None = None, css_path: CSSPathType | None = None,
                 watch_css: bool = False, ansi_color: bool = False):
        self.config = config
        super().__init__(driver_class, css_path, watch_css, ansi_color)

    def compose(self):
        defaults = cast(dict[str, Any], self.config.get('defaults', {}))

        for w_id, conf in cast(dict[str, dict[str, Any]], self.config['mods']).items():
            if conf is None: conf = {}

            if not conf.get('enabled', True): continue

            for k, v in defaults.items():
                conf.setdefault(k, v)

            mod = conf.get('type', w_id.split('%')[0])

            if 'position' in conf:
                conf['window'] = {
                    'y': sum(self.config['grid']['rows'][:conf['position']['top']]),
                    'x': sum(self.config['grid']['columns'][:conf['position']['left']]),
                    'h': sum(self.config['grid']['rows'][
                             conf['position']['top']:conf['position']['top'] + conf['position']['height']]),
                    'w': sum(self.config['grid']['columns'][
                             conf['position']['left']:conf['position']['left'] + conf['position']['width']]),
                }

            coords = Coordinates(conf['window']['h'], conf['window']['w'], conf['window'].get('y', 0),
                                 conf['window'].get('x', 0))

            try:
                #a VERY UGLY hack to allow importing libvirt module without loading its library if running through
                # remote connection
                # 0. just to be sure no one is messing with environment variabled, remove the variable that skips the import phase
                os.environ.pop('__PYD_SKIP_OPTIONAL_IMPORTS__', None)
                # 1. if running through remote connection allow skipping imports
                if 'remote_host' in conf:
                    os.environ['__PYD_SKIP_OPTIONAL_IMPORTS__'] = 'true'
                # 2. do the import as always
                m = import_module('pydashboard.modules.' + mod)
                widget: Module = m.widget(id=w_id, defaults=defaults | conf.pop('defaults', {}), mod_type=mod, **conf)
                # 3. clear the variable
                os.environ.pop('__PYD_SKIP_OPTIONAL_IMPORTS__', None)
                logger.success('Loaded widget {} - {} ({}) [x={coords.x},y={coords.y},w={coords.w},h={coords.h}]', w_id,
                               widget.id, mod, coords=coords)
            except ModuleNotFoundError as e:
                widget = ErrorModule(f"Module '{mod}' not found\n{e.msg}")
            except AttributeError as e:
                widget = ErrorModule(f"Attribute '{e.name}' not found in module {mod}")
            except Exception as e:
                widget = ErrorModule(str(e))

            widget.styles.offset = (coords.x, coords.y)
            widget.styles.width = coords.w
            widget.styles.height = coords.h
            widget.styles.position = "absolute"
            widget.styles.overflow_x = "hidden"
            widget.styles.overflow_y = "hidden"
            yield widget

            try:
                self.ready_hooks[w_id] = widget.on_ready
            except AttributeError:
                pass

            if hasattr(widget, 'ready_hooks'):
                self.ready_hooks.update(widget.ready_hooks)

    def on_ready(self):
        self.signal.clear()
        for key, hook in self.ready_hooks.items():
            t = Thread(target=hook, args=(self.signal,), name=key)
            self.modules_threads.append(t)
            t.start()
        self.ready_hooks.clear()

    def on_exit_app(self):
        logger.info('Stopping module threads')
        self.signal.set()
        while self.modules_threads:
            self.modules_threads.pop().join()
        logger.info('Terminating remote connections')
        SessionManager.close_all()


def main():
    from loguru import logger

    parser = ArgumentParser()
    parser.add_argument('config', type=Path, default=Path.home()/'.config/pydashboard/config.yml', nargs='?')
    parser.add_argument('--log', type=Path, required=False)
    parser.add_argument('--debug', action=BooleanOptionalAction)
    args = parser.parse_args()

    pattern = re.compile(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")
    def _standardize_item(d, key, value):
        if type_util.is_string(key):
            # https://stackoverflow.com/a/12867228/2096218
            norm_key = pattern.sub(r"_\1", key).lower()
            rename(d, key, norm_key)

    _config = benedict(args.config, format='yaml', keypath_separator=None)
    _config.traverse(_standardize_item)

    debug_logger = {'level': 'TRACE', 'backtrace': True, 'diagnose': True} if args.debug else \
        {'level': 'INFO', 'backtrace': False, 'diagnose': False}

    logger.remove()

    log_format = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                  "<level>{level: <8}</level> | <cyan>{extra[module]}</cyan> | "
                  "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    if args.log is not None:
        if args.log.is_dir():
            args.log /= 'pydashboard.log'
        logger.add(args.log, **debug_logger, format=log_format, rotation="weekly")
    else:
        try:
            logger.add(Path.home()/'.pydashboard/log/pydashboard.log', **debug_logger, format=log_format, rotation="weekly")
        except:
            logger.add(args.config.parent / 'log/pydashboard.log', **debug_logger, format=log_format, rotation="weekly")

    # noinspection PyShadowingNames
    logger = logger.bind(module="MainApp")

    logger.info('Starting pydashboard')

    main_app = MainApp(config=_config, ansi_color=_config.get('ansi_color', False))

    def reloader(cfg_file, app: MainApp):
        try:
            for changes in watch(cfg_file, stop_event=app.signal):
                # it's actually possible to use app.signal as a stop event because it would be fired only in two cases:
                # - normal shutdown: in such case we only need to stop the watcher
                # - configuration reload: in such case the event is fired from the app.exit() method below and
                #                         it will eventually become useless since the whole terminal is being replaced
                logger.success("{} changed on disk, reloading", cfg_file)
                logger.debug(changes)
                app.exit()

                os.execv(sys.executable, ['python'] + sys.argv)
        finally:
            app.exit()

    app_thread = Thread(target=reloader, args=(args.config, main_app), name='AppReloader')
    app_thread.start()

    main_app.run()
    logger.info('Exiting')


if __name__ == "__main__":
    main()
