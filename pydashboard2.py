from datetime import datetime
from operator import itemgetter
from typing import List
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Digits
from rich.text import Text
# from modules import clock

class TimeDisplay(Digits):
    DEFAULT_CSS = """
        Widget{
            border: tall yellow;
        }
    """
    """A widget to display elapsed time."""
    def compose(self):
        # self.styles.border = None #("hidden", "blue")
        # self.styles.border_bottom = "round", "yellow"
        self.styles.width = "auto"
        self.styles.position = "absolute"
        # self.styles.offset = 5, 5
        self.border_title = "Orologio"
        self.styles.border_title_color = self.styles.border_top[1]
        self.styles.border_title_background = "black"
        self.border_subtitle = None #"sottotitolo"
        self.styles.border_subtitle_color = self.styles.border_bottom[1]
        yield from super().compose()
        self.update_clock()
        self.set_interval(1, self.update_clock)
        # self.update("99:99:99")

    # def on_ready(self) -> None:

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.update(f"{clock:%H:%M:%S}")


class StopwatchApp(App):
    DEFAULT_CSS = """
        Widget Widget {
            border: round;
            width: auto;
            position: absolute;
        }
    """
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # yield Header()
        # yield Footer()
        # yield TimeDisplay('00:00:00')
        s= Static(markup(Text.from_ansi("I see a \033[1;31mred door, and I want it painted \033[1;30mblack [yellow]Ciao[/yellow]")))
        s.styles.width="50%"
        yield s

    
def markup(self) -> str:
    """Get console markup to render this Text.

    Returns:
        str: A string potentially creating markup tags.
    """
    # from .markup import escape

    output: List[str] = []

    plain = self.plain
    markup_spans = [
        (0, False, self.style),
        *((span.start, False, span.style) for span in self._spans),
        *((span.end, True, span.style) for span in self._spans),
        (len(plain), True, self.style),
    ]
    markup_spans.sort(key=itemgetter(0, 1))
    position = 0
    append = output.append
    for offset, closing, style in markup_spans:
        if offset > position:
            append(plain[position:offset])
            position = offset
        if style:
            append(f"[/{style}]" if closing else f"[{style}]")
    markup = "".join(output)
    return markup




if __name__ == "__main__":
    app = StopwatchApp()
    app.run()