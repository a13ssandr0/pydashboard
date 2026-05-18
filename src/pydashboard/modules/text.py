from typing import Any, Literal

import rich.text

from pydashboard.containers import BaseModule


class Text(BaseModule):
    def __init__(
            self,
            *,
            text: str,
            ansi: bool = False,
            align: Literal["start", "left", "center", "end", "right", "justify"] = "start",
            opacity: float | str = 1.0,
            overflow: Literal["clip", "fold", "ellipsis"] = "fold",
            wrap: bool = True,
            style: str = "none",
            **kwargs: Any
    ):
        """
        Display some static text.
        Supports "[Rich](https://rich.readthedocs.io/en/stable/markup.html#syntax)" markup, emojis (Unicode and [emoji codes](https://rich.readthedocs.io/en/latest/markup.html#emoji)) and ANSI escaped text.
        !!! note
            This widget totally ignores `refresh_interval`: static text does not need to be updated.

        Args:
            text: String to be printed
            ansi: Enables "[ANSI](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797)" escaped text support (emoji codes are not supported in this mode, only Unicode)
            align: Text alignment, "start" and "end" will support RTL layouts in the future.
            opacity: Opacity of the text (0 to 1 o 0% to 100%)
            overflow: Text overflow mode
            wrap: Enable word wrapping
            style: [Base style](https://rich.readthedocs.io/en/stable/style.html) for text
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(text=text, ansi=ansi, align=align, opacity=opacity, overflow=overflow, wrap=wrap, style=style,
                         **kwargs)

        self.inner.styles.width = "100%"
        self.inner.styles.text_align = align
        self.inner.styles.text_opacity = opacity
        self.inner.styles.text_overflow = overflow
        self.inner.styles.text_wrap = "wrap" if wrap else "nowrap"
        self.inner.styles.text_style = style

        if ansi:
            text = rich.text.Text.from_ansi(text)
        else:
            # needed only to add emoji string support (es: `:red_heart-emoji:`)
            text = rich.text.Text.from_markup(text, emoji=True)

        self.inner.update(text)

    def on_ready(self, _):
        pass


widget = Text
