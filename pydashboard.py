import curses
from argparse import ArgumentParser
from importlib import import_module, invalidate_caches, reload
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Any, NamedTuple, cast

import yaml
from durations import Duration
from watchfiles import run_process

from basemod import BaseModule, ErrorModule

from textual.app import App


Coordinates = NamedTuple('Coordinates', [
    ('h', int), ('w', int), ('y', int), ('x', int),
])
threads:list[Thread] = []
imported_modules = set()

def main(scr: curses.window, config: dict):
    scr.clear()
    curses.curs_set(0)
    # curses.start_color()
    curses.use_default_colors()
    # for j in range (0, curses.COLORS):
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, curses.COLOR_WHITE)
    
    windows:list[tuple[curses.window, int, int, int, int]] = []
    
    defaults = cast(dict[str, Any], config.get('defaults'))
    # grid_c = cast(list[int], config.get('grid', {'columns': None}).get('columns'))
    # grid_r = cast(list[int], config.get('grid', {'rows': None}).get('rows'))
    
    for key, conf in cast(dict[str,dict[str,Any]], config['mods']).items():
        if not conf.get('enabled', True): continue
        
        for k, v in defaults.items():
            conf.setdefault(k ,v)
        
        mod = conf.get('type', key)
        
        if isinstance(conf.get('refreshInterval'), str):
            conf['refreshInterval'] = round(Duration(conf['refreshInterval']).to_seconds())
        
        if 'position' in conf:
            conf['window'] = {
                'y': sum(config['grid']['rows'][:conf['position']['top']]),
                'x': sum(config['grid']['columns'][:conf['position']['left']]),
                'h': sum(config['grid']['rows'][conf['position']['top']:conf['position']['top']+conf['position']['height']]),
                'w': sum(config['grid']['columns'][conf['position']['left']:conf['position']['left']+conf['position']['width']]),
            }
        
        coords = Coordinates(conf['window']['h'], conf['window']['w'], conf['window'].get('y', 0), conf['window'].get('x', 0))
        
        out_win = curses.newwin(coords.h, coords.w, coords.y, coords.x)
        # for sake of simplicity we get the integer value from a boolean to set
        # the border (instead of using an if/else), 
        # this has the side effect of allowing the user to add a padding, 
        # that's not a bug, that's a feature, but we have to make sure the 
        # border value is always positive
        offset = abs(int(conf.get('border', True)))
        conf['border'] = not not offset
        
        win = curses.newpad(100, 100)
        
        try:
            m = import_module('modules.'+mod)
            imported_modules.add(m)
            widget:BaseModule = m.widget(out_win=out_win, win=win, **conf)
            
            threads.append(t:=Thread(target=widget, name=widget.title or key))
            t.start()
        except (ModuleNotFoundError, AttributeError):
            ErrorModule(out_win=out_win, win=win, **conf)(f"Module '{mod}' not found")
        finally:
            windows.append((out_win, coords.h, coords.w, coords.y, coords.x))
            windows.append((win, coords.y+coords.h-offset-1, coords.x+coords.w-offset-1, coords.y+offset, coords.x+offset))
            
        
    def upd_win(windows:list[curses.window]):
        while True:
            for win, h, w, y, x in windows:
                try:
                    win.noutrefresh()
                except:
                    cast(curses.window, win).noutrefresh( 0,0, y,x, h,w)
            curses.doupdate()
            sleep(.5)
    
    threads.append(t:=Thread(target=upd_win, args=(windows,), name='refresh'))
    t.start()
    t.join()
        
    # while True:
    #     match scr.getch():
    #         case ord('q'):
    #             raise KeyboardInterrupt()
        
        
class MainApp(App):
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
            
            # if isinstance(conf.get('refreshInterval'), str):
            #     conf['refreshInterval'] = round(Duration(conf['refreshInterval']).to_seconds())
            
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
                widget:BaseModule = m.widget(**conf)
            except (ModuleNotFoundError, AttributeError):
                widget = ErrorModule(f"Module '{mod}' not found")
            
            widget.styles.offset = (coords.x, coords.y)
            widget.styles.width = coords.w
            widget.styles.height = coords.h
            widget.styles.position = "absolute"
            widget.styles.overflow_x = "hidden"
            widget.styles.overflow_y = "hidden"
            yield widget




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
