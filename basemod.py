from typing import Literal, NamedTuple

from durations import Duration
from textual.containers import ScrollableContainer
from textual.widgets import Static

Coordinates = NamedTuple('Coordinates', [
    ('h', int), ('w', int), ('y', int), ('x', int),
])


class BaseModule(ScrollableContainer):
    def __init__(self, *,
                 id:str=None,
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

        
    def __call__(self) -> str:
        """Method called each time the module has to be updated"""
        raise NotImplementedError('Stub')
    
    def update(self):
        txt=self()
        self.inner.update('\n'.join([l for l in str(txt if txt is not None else '').splitlines()]))
    
    def compose(self):
        self.inner = Static()
        self.inner.styles.width = "auto"
        self.inner.styles.height = "auto"
        self.update()
        self.set_interval(self.refreshInterval, self.update)
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
    
    def compose(self):
        self.border_title = "Module error"
        yield from super().compose()