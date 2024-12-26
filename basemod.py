from curses import window, error
import curses
from time import sleep
from typing import Literal
from stransi import Ansi, Escape
from textual.widgets import Static
from textual.containers import ScrollableContainer
from durations import Duration
import os


class BaseModule(ScrollableContainer):
    
    # def __init_subclass__(cls) -> None:
    #     cls.__init__.__kwdefaults__['title'] = cls.__name__
    
    def __init__(self, *,
                 refreshInterval:int|float|str=None, 
                 border=("round", "white"),
                 title:str=None,
                 title_align:Literal['left','center','right']="center",
                 title_background:str=None,
                 title_color:str="white",
                 title_style:str=None,
                 subtitle:str=None,
                 subtitle_align:Literal['left','center','right']="center",
                 subtitle_background:str=None,
                 subtitle_color:str="white",
                 subtitle_style:str=None,
                 id:str=None,
                 **kwargs):
        """Init module and load config"""
        super().__init__(id=id)
        
        if isinstance(refreshInterval, str):
            refreshInterval = Duration(refreshInterval).to_seconds()
        self.refreshInterval = refreshInterval
        
        if border:
            self.styles.border = border or "none"
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
            
            
        # if title is None: title=self.__class__.__name__
        # self._title = title
        # self._title_color = title_color
        # self.__do_border_title__()
        
    def __call__(self) -> str:
        """Method called each time the module has to be updated"""
        raise NotImplementedError('Stub')
    
    def update(self):
        self.inner.update('\n'.join([l+(' '*os.get_terminal_size().columns) for l in str(self()).splitlines()]))
    
    def compose(self):
        self.inner = Static()
        self.inner.styles.width = "auto"
        self.inner.styles.height = "auto"
        # self.inner.styles.overflow_x = "hidden"
        # self.inner.styles.overflow_y = "hidden"
        self.update()
        self.set_interval(self.refreshInterval, self.update)
        yield self.inner
        
    # def __do_border_title__(self):
    #     title = ' ' + self._title[:self.out_win.getmaxyx()[1]].strip() + ' '
    #     self.out_win.clear()
        
    #     if self._border == True:
    #         self.out_win.attrset(colors(self._border_color))
    #         self.out_win.box()
    #         self.out_win.attrset(-1)
        
    #     if title.strip():
    #         self.out_win.addstr(0, (self.out_win.getmaxyx()[1]-len(title))//2, title, colors(self._title_color))
        
        
    # def __call__(self):
    #     while True:
    #         text = parse_str(self.__run__())            
    #         self.win.clear()
    #         try:
    #             self.win.addstr(text)
    #         except error:
    #             pass
    #         sleep(self.refresh)
            
    # @property
    # def border(self):
    #     return self._border
    
    # @border.setter
    # def border(self, border):
    #     self._border = border
    #     self.__do_border_title__()
            
    # @property
    # def border_color(self):
    #     return self._border_color
    
    # @border_color.setter
    # def border_color(self, border_color):
    #     self._border_color = border_color
    #     self.__do_border_title__()
        
    # @property
    # def title(self):
    #     return self._title
    
    # @title.setter
    # def title(self, title):
    #     self._title = title
    #     self.__do_border_title__()
        
    # @property
    # def title_color(self):
    #     return self._title_color
    
    # @title_color.setter
    # def title_color(self, title_color):
    #     self._title_color = title_color
    #     self.__do_border_title__()





class ErrorModule(Static):
    DEFAULT_CSS = """
        ErrorModule {
            border: heavy red;
            border-title-align: center;
            border-title-color: red;
            color: red;
        }
    """
    
    def compose(self):
        self.border_title = "Module error"
        yield from super().compose()