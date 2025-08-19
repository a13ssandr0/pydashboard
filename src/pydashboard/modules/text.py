from typing import Any, Literal

import rich.text

from pydashboard.containers import BaseModule


class Text(BaseModule):
    def __init__(
            self,
            *,
            text: str,
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
        Display some static text.
        !!! note
            This widget totally ignores `refresh_interval`: static text does not need to be updated.

        Args:
            text: String to be printed
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
        super().__init__(text=text, mode=mode, style=style, emoji=emoji, emoji_variant=emoji_variant, justify=justify,
                         overflow=overflow, no_wrap=no_wrap, end=end, tab_size=tab_size, **kwargs)

        if mode == "rich":
            text = rich.text.Text.from_markup(
                    text,
                    style=style,
                    emoji=emoji,
                    emoji_variant=emoji_variant,
                    justify=justify,
                    overflow=overflow,
                    end=end,
            )
        elif mode == "ansi":
            text = rich.text.Text.from_ansi(
                    text,
                    style=style,
                    justify=justify,
                    overflow=overflow,
                    no_wrap=no_wrap,
                    end=end,
                    tab_size=tab_size)
        else:
            text = rich.text.Text(
                    text,
                    style=style,
                    justify=justify,
                    overflow=overflow,
                    no_wrap=no_wrap,
                    end=end,
                    tab_size=tab_size,
            )

        self.inner.update(text)

    def on_ready(self, _):
        pass


widget = Text
