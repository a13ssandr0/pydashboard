from rich.text import Text

from pydashboard.containers import BaseModule
from pydashboard.utils.bars import create_bar
from pydashboard.utils.types import Size


class Demo(BaseModule):
    def __call__(self, size: Size):
        text = ("[bold red]alert![/bold red] Something happened\n"
        "[bold italic yellow on red blink]This text is impossible to read\n"
        "[bold red]Bold and red[/] not bold or red\n"
        "[bold]Bold[italic] bold and italic [/bold]italic[/italic]\n")

        text += create_bar(size[1], 69, 'foo', 'bar', 'yellow')

        text += Text.from_ansi("\n\033[1mThis text is formatted with ansi codes\033[0m\n").markup

        self.set('styles.border', ('round', 'red'))

        return text


widget = Demo