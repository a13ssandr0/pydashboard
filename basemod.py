from time import sleep
from typing import Literal, NamedTuple

from durations import Duration
from textual.containers import ScrollableContainer
from textual.widgets import Static
from rich.text import Text
import traceback
from textual.css.types import AlignHorizontal, AlignVertical
from textual.css._style_properties import BorderDefinition, ColorProperty, StyleFlagsProperty
from threading import Event

from helpers.strings import markup

Coordinates = NamedTuple('Coordinates', [
    ('h', int), ('w', int), ('y', int), ('x', int),
])


class BaseModule(ScrollableContainer):
    def __init__(self, *,
                 coords:Coordinates,
                 id:str=None,
                 refreshInterval:int|float|str=None,
                 align_horizontal:AlignHorizontal="left",
                 align_vertical:AlignVertical="top",
                 color:ColorProperty=None,
                 border:BorderDefinition=("round", "white"),
                 title:str=None,
                 title_align:AlignHorizontal="center",
                 title_background:ColorProperty=None,
                 title_color:ColorProperty="white",
                 title_style:StyleFlagsProperty=None,
                 subtitle:str=None,
                 subtitle_align:AlignHorizontal="right",
                 subtitle_background:ColorProperty=None,
                 subtitle_color:ColorProperty="white",
                 subtitle_style:StyleFlagsProperty=None,
                 **kwargs):
        """Init module and load config"""
        super().__init__(id=id)
        
        self.content_width = coords.w
        self.content_height = coords.h
        
        if isinstance(refreshInterval, str):
            refreshInterval = Duration(refreshInterval).to_seconds()
        self.refreshInterval = refreshInterval
        
        self.styles.align_horizontal = align_horizontal
        self.styles.align_vertical = align_vertical
        
        self.styles.color = color
        
        if border:
            self.content_width -= 2
            self.content_height -= 2
            self.styles.border = tuple(border) or "none"
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

        self.inner = Static()
        self.inner.styles.width = "auto"
        self.inner.styles.height = "auto"

    def __post_init__(self):
        """Perform post initialization tasks"""
        pass

    def __call__(self) -> str:
        """Method called each time the module has to be updated"""
        raise NotImplementedError('Stub')
    
    def update(self):
        try:
            result = self()
            if result is None:
                self.inner.update('')
            else:
                self.inner.update(markup(Text.from_ansi(str(result))))
        except:
            self.inner.update('\n'.join(traceback.format_exc().splitlines()[-self.content_height:]))
    
    def on_ready(self, signal:Event):
        self.__post_init__()
        # self.update()
        # self.set_interval(self.refreshInterval, self.update)
        while not signal.is_set():
            self.update()
            for _ in range(round(self.refreshInterval)):
                if signal.is_set(): return
                sleep(1)
        
    def compose(self):
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