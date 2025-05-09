from argparse import ArgumentParser, BooleanOptionalAction
from importlib import import_module, invalidate_caches, reload
from pathlib import Path
from threading import Event, Thread
from typing import Any, cast

import yaml
from loguru import logger
from textual.app import App

from containers import BaseModule, Coordinates, ErrorModule

imported_modules = set()



class MainApp(App):
    CSS = r"""Screen {overflow: hidden hidden;}"""
    
    ready_hooks = {}
    
    def compose(self):

        invalidate_caches()
        for m in imported_modules: reload(m)
        
        defaults = cast(dict[str, Any], self.config.get('defaults', {}))
        
        for w_id, conf in cast(dict[str,dict[str,Any]], self.config['mods']).items():
            if conf is None: conf = {}
            
            if not conf.get('enabled', True): continue
            
            for k, v in defaults.items():
                conf.setdefault(k ,v)
            
            mod = conf.get('type', w_id.split('%')[0])
            
            if 'position' in conf:
                conf['window'] = {
                    'y': sum(self.config['grid']['rows'][:conf['position']['top']]),
                    'x': sum(self.config['grid']['columns'][:conf['position']['left']]),
                    'h': sum(self.config['grid']['rows'][conf['position']['top']:conf['position']['top']+conf['position']['height']]),
                    'w': sum(self.config['grid']['columns'][conf['position']['left']:conf['position']['left']+conf['position']['width']]),
                }
            
            coords = Coordinates(conf['window']['h'], conf['window']['w'], conf['window'].get('y', 0), conf['window'].get('x', 0))
            
            try:
                m = import_module('modules.'+mod)
                imported_modules.add(m)
                widget:BaseModule = m.widget(id=w_id, defaults=defaults|conf.pop('defaults',{}), **conf)
                logger.success('Loaded widget {} - {} ({}) [x={coords.x},y={coords.y},w={coords.w},h={coords.h}]', w_id, widget.id, mod, coords=coords)
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
    
    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config', type=Path)
    parser.add_argument('--log', type=Path, required=False)
    parser.add_argument('--debug', action=BooleanOptionalAction)
    args = parser.parse_args()

    with open(args.config) as file:
        config = yaml.safe_load(file)

    debug_logger = {'level': 'TRACE', 'backtrace': True, 'diagnose': True} if args.debug else \
                   {'level': 'INFO', 'backtrace': False, 'diagnose': False}

    logger.remove()    
    if args.log is not None:
        logger.add(args.log, **debug_logger, rotation="weekly")
    else:
        try:
            logger.add(args.config.parent/'log/pydashboard.log', **debug_logger, rotation="weekly")
        except:
            logger.add('~/.pydashboard/log/pydashboard.log', **debug_logger, rotation="weekly")

    logger.info('Starting pydashboard')

    app = MainApp(ansi_color=config.get('ansi_color', False))
    app.config = config
    app.run()
    logger.info('Exiting')
    if args.debug:
        #wait for user input to allow reading exceptions
        input()
