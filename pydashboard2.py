from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Digits


class TimeDisplay(Digits):
    """A widget to display elapsed time."""
    # def compose(self):
    #     # self.styles.border = ("round", "blue")
    #     # self.styles.width = "auto"
    #     # self.styles.position = "absolute"
    #     # self.styles.offset = 5, 5
    #     yield from super().compose()


class StopwatchApp(App):
    DEFAULT_CSS = """
        Widget Widget {
            border: round white;
            width: auto;
            position: absolute;
        }
    """
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # yield Header()
        # yield Footer()
        yield TimeDisplay('00:00:00')
        yield Static("I see a \033[1;31mred\033[;39m door, and I want it painted \033[1;30mblack\033[;39m Ciao")

    def on_ready(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%H:%M:%S}")


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()