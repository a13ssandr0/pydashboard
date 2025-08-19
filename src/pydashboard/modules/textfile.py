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
            mode: Literal["plain", "rich", "ansi"] = "plain",
            style: str = "",
            emoji: bool = True,
            emoji_variant: Literal["emoji", "text"] = None,
            justify: Literal["default", "left", "center", "right", "full"] = None,
            overflow: Literal["fold", "crop", "ellipsis", "ignore"] = None,
            no_wrap: bool = None,
            end: str = "\n",
            tab_size: int = None,
            **kwargs: Any
    ):
        """
        Display the content of a text file.

        Args:
            title: if not set or null defaults to file path
            path: Full path to file to be printed
            mode: One of "plain", "[rich](https://rich.readthedocs.io/en/stable/markup.html#syntax)" or "[ansi](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797)"
            style: [Base style](https://rich.readthedocs.io/en/stable/style.html) for text
            emoji: Allow rendering emoji codes
            emoji_variant: Emoji variant, either "text" or "emoji"
            justify: Justify method: "left", "center", "full", "right"
            overflow: Overflow method: "crop", "fold", "ellipsis"
            no_wrap: Disable text wrapping
            end: Character to end text with
            tab_size: Number of spaces per tab, or ``None`` to use ``console.tab_size``
            **kwargs: See [BaseModule](../containers/basemodule.md)


        Available parameters for each mode:

        Name            | "plain" | "rich" | "ansi"
        ----------------|---------|--------|--------
        `style`         |    ✅   |   ✅   |   ✅
        `emoji`         |    ❌   |   ✅   |   ❌
        `emoji_variant` |    ❌   |   ✅   |   ❌
        `justify`       |    ✅   |   ✅   |   ✅
        `overflow`      |    ✅   |   ✅   |   ✅
        `no_wrap`       |    ✅   |   ❌   |   ✅
        `end`           |    ✅   |   ✅   |   ✅
        `tab_size`      |    ✅   |   ❌   |   ✅

        !!! info
            Parameters marked with ❌ will be ignored.
        """
        if title is None:
            title = path

        super().__init__(title=title, path=path, mode=mode, style=style, emoji=emoji, emoji_variant=emoji_variant,
                         justify=justify, overflow=overflow, no_wrap=no_wrap, end=end, tab_size=tab_size, **kwargs)
        self.path = path
        self.mode = mode
        self.style = style
        self.emoji = emoji
        self.emoji_variant = emoji_variant
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size

    def __call__(self):
        with open(self.path) as file:
            text = file.read()

        if self.mode == "rich":
            text = rich.text.Text.from_markup(
                    text,
                    style=self.style,
                    emoji=self.emoji,
                    emoji_variant=self.emoji_variant,
                    justify=self.justify,
                    overflow=self.overflow,
                    end=self.end,
            )
        elif self.mode == "ansi":
            text = rich.text.Text.from_ansi(
                    text,
                    style=self.style,
                    justify=self.justify,
                    overflow=self.overflow,
                    no_wrap=self.no_wrap,
                    end=self.end,
                    tab_size=self.tab_size)
        else:
            text = rich.text.Text(
                    text,
                    style=self.style,
                    justify=self.justify,
                    overflow=self.overflow,
                    no_wrap=self.no_wrap,
                    end=self.end,
                    tab_size=self.tab_size,
            )

        return text


widget = TextFile
