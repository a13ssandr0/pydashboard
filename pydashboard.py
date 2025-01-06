from argparse import ArgumentParser
import asyncio
from importlib import import_module, invalidate_caches, reload
from inspect import isawaitable, iscoroutinefunction
from pathlib import Path
from typing import Any, cast

import yaml
from textual.app import App

from basemod import BaseModule, Coordinates, ErrorModule

imported_modules = set()

        
        
class MainApp(App):
    CSS = """
        Screen {
            overflow: hidden hidden;
        }
    """
    
    ready_hooks = []
    
    def compose(self):
        with open(self.config) as file:
            config = yaml.safe_load(file)

        invalidate_caches()
        for m in imported_modules: reload(m)
        
        defaults = cast(dict[str, Any], config.get('defaults'))
        
        for key, conf in cast(dict[str,dict[str,Any]], config['mods']).items():
            if not conf.get('enabled', True): continue
            
            for k, v in defaults.items():
                conf.setdefault(k ,v)
            
            mod = conf.get('type', key)
            
            if 'position' in conf:
                conf['window'] = {
                    'y': sum(config['grid']['rows'][:conf['position']['top']]),
                    'x': sum(config['grid']['columns'][:conf['position']['left']]),
                    'h': sum(config['grid']['rows'][conf['position']['top']:conf['position']['top']+conf['position']['height']]),
                    'w': sum(config['grid']['columns'][conf['position']['left']:conf['position']['left']+conf['position']['width']]),
                }
            
            coords = Coordinates(conf['window']['h'], conf['window']['w'], conf['window'].get('y', 0), conf['window'].get('x', 0))
            
            try:
                m = import_module('modules.'+mod)
                imported_modules.add(m)
                widget:BaseModule = m.widget(coords=coords, id=key, **conf)
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
                self.ready_hooks.append(widget.on_ready)
            except AttributeError:
                pass

    async def on_ready(self):
        # for hook in self.ready_hooks:
        #     await hook()
        await asyncio.gather(*[hook() for hook in self.ready_hooks if iscoroutinefunction(hook)])


# def reload_handler(args):
#     with open(args.config) as file:
#         config = yaml.safe_load(file)

#     invalidate_caches()
#     for m in imported_modules: reload(m)

#     try:
#         curses.wrapper(main, config)
#     except KeyboardInterrupt:
#         print('Exiting')
#         exit()
    
    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    
    # run_process(
    #     args.config,
    #     __file__,
    #     Path(__file__).parent/'modules',
    #     Path(__file__).parent/'basemod.py',
    #     target=reload_handler, args=args)

    app = MainApp()
    app.config = args.config
    app.run()
    input()
