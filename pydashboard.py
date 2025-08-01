import threading
from argparse import ArgumentParser, BooleanOptionalAction
from importlib import import_module
from pathlib import Path
from threading import Event, Thread
from typing import Any, Type, cast

import yaml
from loguru import logger
from textual._path import CSSPathType
from textual.app import App
from textual.driver import Driver

from containers import ErrorModule, GenericModule
from utils.ssh import SessionManager
from utils.types import Coordinates


class MainApp(App):
    CSS = r"""Screen {overflow: hidden hidden;}"""
    config: dict
    ready_hooks = {}

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
                m = import_module('modules.' + mod)
                widget: GenericModule = m.widget(id=w_id, defaults=defaults | conf.pop('defaults', {}), mod_type=mod,
                                                 **conf)
                logger.success('Loaded widget {} - {} ({}) [x={coords.x},y={coords.y},w={coords.w},h={coords.h}]', w_id,
                               widget.id, mod, coords=coords)
            except ModuleNotFoundError as e:
                widget = ErrorModule(f"Module '{mod}' not found\n{e.msg}")
            except AttributeError as e:
                widget = ErrorModule(f"Attribute '{e.name}' not found in module {mod}")

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
        self.signal = Event()
        for key, hook in self.ready_hooks.items():
            Thread(target=hook, args=(self.signal,), name=key).start()

    def on_exit_app(self):
        logger.info('Stopping module threads')
        self.signal.set()
        logger.info('Terminating remote connections')
        SessionManager.close_all()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config', type=Path)
    parser.add_argument('--log', type=Path, required=False)
    parser.add_argument('--debug', action=BooleanOptionalAction)
    args = parser.parse_args()

    with open(args.config) as file:
        _config = yaml.safe_load(file)

    debug_logger = {'level': 'TRACE', 'backtrace': True, 'diagnose': True} if args.debug else \
        {'level': 'INFO', 'backtrace': False, 'diagnose': False}

    logger.remove()

    log_format = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                  "<level>{level: <8}</level> | <cyan>{extra[module]}</cyan> | "
                  "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    if args.log is not None:
        logger.add(args.log, **debug_logger, format=log_format, rotation="weekly")
    else:
        try:
            logger.add(args.config.parent / 'log/pydashboard.log', **debug_logger, format=log_format, rotation="weekly")
        except:
            logger.add('~/.pydashboard/log/pydashboard.log', **debug_logger, format=log_format, rotation="weekly")

    logger = logger.bind(module="MainApp")

    logger.info('Starting pydashboard')

    app = MainApp(config=_config, ansi_color=_config.get('ansi_color', False))
    app.run()
    logger.info('Exiting')
    if args.debug:
        # wait for user input to allow reading exceptions
        input("Press any key to continue...")
        for thread in threading.enumerate():
            print(thread.name)
