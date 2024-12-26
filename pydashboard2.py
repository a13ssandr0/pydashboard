from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Digits
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
        yield TimeDisplay('00:00:00')
        # s= Static("I see a \033[1;31mred\033[;39m door, and I want it painted \033[1;30mblack\033[;39m Ciao", expand=True)
        # s.styles.width="50%"
        # yield s

    


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()