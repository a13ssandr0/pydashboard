from curses import window, error
from time import sleep

class BaseModule():
    
    # def __init_subclass__(cls) -> None:
    #     cls.__init__.__defaults__
    
    def __init__(self, *, out_win:window, win:window, refreshInterval:int=None, border=True, title:str=None, **kwargs):
        """Init module and load config"""
        self.out_win = out_win
        self.win = win
        self.refresh = refreshInterval
        self.border = border
        if title is None: title=self.__class__.__name__
        self.title = title
        
    def __run__(self):
        """Method called each time the module has to be updated"""
        raise NotImplementedError('Stub')
        
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, title):
        self._title = title
        title = ' ' + self._title[:self.out_win.getmaxyx()[1]].strip() + ' '
        self.out_win.clear()
        if self.border: self.out_win.border()
        if title.strip():
            self.out_win.addstr(0, (self.out_win.getmaxyx()[1]-len(title))//2, title)
        # self.out_win.refresh()
        
    def __call__(self):
        while True:
            self.win.clear()
            try:
                self.win.addstr(self.__run__())
            except error:
                pass
            # self.win.refresh()
            sleep(self.refresh)