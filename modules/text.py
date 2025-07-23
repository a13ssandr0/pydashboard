from typing import List, Literal, Optional, Union

import rich.text
from rich.emoji import EmojiVariant
from rich.style import Style
from rich.text import Span

from containers import BaseModule


class Text(BaseModule):
    def __init__(
            self,
            *,
            text: str = "",
            mode: Literal["plain", "rich", "ansi"] = "plain",
            style: Union[str, Style] = "",
            emoji: bool = True,
            emoji_variant: Optional[EmojiVariant] = None,
            align: Optional[Literal["default", "left", "center", "right", "full"]] = None,
            overflow: Optional[Literal["fold", "crop", "ellipsis", "ignore"]] = None,
            no_wrap: Optional[bool] = None,
            end: str = "\n",
            tab_size: Optional[int] = None,
            spans: Optional[List[Span]] = None,
            **kwargs
    ):
        super().__init__(**kwargs)

        if mode == "rich":
            text = rich.text.Text.from_markup(
                    text,
                    style=style,
                    emoji=emoji,
                    emoji_variant=emoji_variant,
                    justify=align,
                    overflow=overflow,
                    end=end,
            )
        elif mode == "ansi":
            text = rich.text.Text.from_ansi(
                    text,
                    style=style,
                    justify=align,
                    overflow=overflow,
                    no_wrap=no_wrap,
                    end=end,
                    tab_size=tab_size)
        else:
            text = rich.text.Text(
                    text,
                    style=style,
                    justify=align,
                    overflow=overflow,
                    no_wrap=no_wrap,
                    end=end,
                    tab_size=tab_size,
                    spans=spans,
            )

        self.inner.update(text)

    def on_ready(self, _):
        pass


widget = Text
