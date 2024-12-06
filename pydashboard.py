import curses
from argparse import ArgumentParser
from pathlib import Path
from threading import Thread
from typing import NamedTuple
import yaml
from watchfiles import run_process
from time import sleep
from importlib import import_module, invalidate_caches

from basemod import BaseModule

Coordinates = NamedTuple('Coordinates', [
    ('h', int), ('w', int), ('y', int), ('x', int),
])
threads:list[Thread] = []


def main(scr: curses.window, config: dict):
    invalidate_caches()
    scr.clear()
    curses.curs_set(0)
    # curses.start_color()
    # curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)

    windows:list[curses.window] = []
    
    for key, conf in config['mods'].items(): 
        mod = conf.get('type', key)
        
        coords = Coordinates(conf['window']['h'], conf['window']['w'], conf['window'].get('y', 0), conf['window'].get('x', 0))
        
        out_win = curses.newwin(coords.h, coords.w, coords.y, coords.x)
        # for sake of simplicity we get the integer value from a boolean to set
        # the border (instead of using an if/else), 
        # this has the side effect of allowing the user to add a padding, 
        # that's not a bug, that's a feature, but we have to make sure the 
        # border value is always positive
        offset = abs(int(conf.get('border', True)))
        win = curses.newwin(coords.h-(2*offset), coords.w-(2*offset), coords.y+offset, coords.x+offset)
        
        widget:BaseModule = import_module('modules.'+mod).widget(out_win=out_win, win=win, **conf)
        
        threads.append(t:=Thread(target=widget, name=widget.title or key))
        t.start()
        windows.append(out_win)
        windows.append(win)
        
    def upd_win(windows:list[curses.window]):
        while True:
            for w in windows: w.refresh()
            sleep(.5)
    
    threads.append(t:=Thread(target=upd_win, args=(windows,), name='refresh'))
    t.start()
    t.join()
        
    # while True:
    #     match scr.getch():
    #         case ord('q'):
    #             raise KeyboardInterrupt()
        
        

    

parser = ArgumentParser()
parser.add_argument('config', type=Path)
args = parser.parse_args()


def reload_handler():
    with open(args.config) as file:
        config = yaml.safe_load(file)

    try:
        curses.wrapper(main, config)
    except KeyboardInterrupt:
        print('Exiting')
        exit()
    
    
if __name__ == "__main__":
    run_process(
        args.config,
        # __file__,
        Path(__file__).parent/'modules',
        Path(__file__).parent/'basemod.py',
        target=reload_handler)
