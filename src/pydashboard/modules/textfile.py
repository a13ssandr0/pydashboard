from typing import Any, Literal

import rich.text

from pydashboard.containers import BaseModule


# noinspection PyPep8Naming
class TextFile(BaseModule):
    def __init__(
            self,
            *,
            path: str,
            title: str = None,
            ansi: bool = False,
            align: Literal["start", "left", "center", "end", "right", "justify"] = "start",
            opacity: float | str = 1.0,
            overflow: Literal["clip", "fold", "ellipsis"] = "fold",
            wrap: bool = True,
            style: str = "none",
            **kwargs: Any
    ):
        """
        Display the content of a text file.

        Args:
            title: if not set or null defaults to file path
            path: Full path to file to be printed
            ansi: Enables "[ANSI](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797)" escaped text support (emoji codes are not supported in this mode, only Unicode)
            align: Text alignment, "start" and "end" will support RTL layouts in the future.
            opacity: Opacity of the text (0 to 1 o 0% to 100%)
            overflow: Text overflow mode
            wrap: Enable word wrapping
            style: [Base style](https://rich.readthedocs.io/en/stable/style.html) for text
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        if title is None:
            title = path

        super().__init__(title=title, path=path, ansi=ansi, align=align, opacity=opacity, overflow=overflow, wrap=wrap,
                         style=style, **kwargs)
        self.path = path
        self.ansi = ansi
        self.inner.styles.width = "100%"
        self.inner.styles.text_align = align
        self.inner.styles.text_opacity = opacity
        self.inner.styles.text_overflow = overflow
        self.inner.styles.text_wrap = "wrap" if wrap else "nowrap"
        self.inner.styles.text_style = style

    def __call__(self):
        with open(self.path) as file:
            text = file.read()

        if self.ansi:
            text = rich.text.Text.from_ansi(text)
        else:
            # needed only to add emoji string support (es: `:red_heart-emoji:`)
            text = rich.text.Text.from_markup(text, emoji=True)
        return text


widget = TextFile
