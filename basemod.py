from curses import window, error
import curses
from time import sleep

_colors = {
    None:       -1,
    'black':    curses.COLOR_BLACK,
    'blue':     curses.COLOR_BLUE,
    'cyan':     curses.COLOR_CYAN,
    'green':    curses.COLOR_GREEN,
    'magenta':  curses.COLOR_MAGENTA,
    'red':      curses.COLOR_RED,
    'white':    curses.COLOR_WHITE,
    'yellow':   curses.COLOR_YELLOW,
}

def colors(color=None):
    return curses.color_pair(_colors[color])



class BaseModule():
    
    # def __init_subclass__(cls) -> None:
    #     cls.__init__.__defaults__
    
    def __init__(self, *, out_win:window, win:window, 
                 refreshInterval:int=None, 
                 border=True, border_color:str=None, 
                 title:str=None, title_color:str=None, **kwargs):
        """Init module and load config"""
        self.out_win = out_win
        self.win = win
        self.refresh = refreshInterval
        self._border = border
        self._border_color = border_color
        if title is None: title=self.__class__.__name__
        self._title = title
        self._title_color = title_color
        self.__do_border_title__()
        
    def __run__(self):
        """Method called each time the module has to be updated"""
        raise NotImplementedError('Stub')
        
    def __do_border_title__(self):
        title = ' ' + self._title[:self.out_win.getmaxyx()[1]].strip() + ' '
        self.out_win.clear()
        
        if self._border == True:
            self.out_win.attrset(colors(self._border_color))
            self.out_win.box()
            self.out_win.attrset(-1)
        
        if title.strip():
            self.out_win.addstr(0, (self.out_win.getmaxyx()[1]-len(title))//2, title, colors(self._title_color))
        
        
    def __call__(self):
        while True:
            self.win.clear()
            try:
                self.win.addstr(str(self.__run__()))
            except error:
                pass
            sleep(self.refresh)
            
    @property
    def border(self):
        return self._border
    
    @border.setter
    def border(self, border):
        self._border = border
        self.__do_border_title__()
            
    @property
    def border_color(self):
        return self._border_color
    
    @border_color.setter
    def border_color(self, border_color):
        self._border_color = border_color
        self.__do_border_title__()
        
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, title):
        self._title = title
        self.__do_border_title__()
        
    @property
    def title_color(self):
        return self._title_color
    
    @title_color.setter
    def title_color(self, title_color):
        self._title_color = title_color
        self.__do_border_title__()





class ErrorModule(BaseModule):
    
    def __init__(self, *, out_win, win, refreshInterval = None, border=True, border_color = None, title = 'Module error', title_color = None, **kwargs):
        super().__init__(out_win=out_win, win=win, refreshInterval=refreshInterval, border=border, border_color='red', title=title, title_color='red', **kwargs)
    
    def __call__(self, msg):
        self.win.clear()
        try:
            self.win.addstr(msg, colors('red'))
        except error:
            pass