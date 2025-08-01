from typing import List, Literal, Optional, Union

import rich.text
from rich.emoji import EmojiVariant
from rich.style import Style
from rich.text import Span

from containers import BaseModule


# noinspection PyPep8Naming
class TextFile(BaseModule):
    def __init__(
            self,
            *,
            path: str = "",
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
            refreshInterval: Literal['never'] | int | float | str = 'never',
            **kwargs
    ):
        super().__init__(path=path, mode=mode, style=style, emoji=emoji, emoji_variant=emoji_variant, align=align,
                         overflow=overflow, no_wrap=no_wrap, end=end, tab_size=tab_size, spans=spans,
                         refreshInterval=refreshInterval, **kwargs)
        self.path = path
        self.mode = mode
        self.style = style
        self.emoji = emoji
        self.emoji_variant = emoji_variant
        self.align = align
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size
        self.spans = spans

    def __call__(self):
        with open(self.path) as file:
            text = file.read()

        if self.mode == "rich":
            text = rich.text.Text.from_markup(
                    text,
                    style=self.style,
                    emoji=self.emoji,
                    emoji_variant=self.emoji_variant,
                    justify=self.align,
                    overflow=self.overflow,
                    end=self.end,
            )
        elif self.mode == "ansi":
            text = rich.text.Text.from_ansi(
                    text,
                    style=self.style,
                    justify=self.align,
                    overflow=self.overflow,
                    no_wrap=self.no_wrap,
                    end=self.end,
                    tab_size=self.tab_size)
        else:
            text = rich.text.Text(
                    text,
                    style=self.style,
                    justify=self.align,
                    overflow=self.overflow,
                    no_wrap=self.no_wrap,
                    end=self.end,
                    tab_size=self.tab_size,
                    spans=self.spans,
            )

        return text


widget = TextFile
