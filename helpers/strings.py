from operator import itemgetter
from typing import List


def ljust(s:str, l:int): return s.ljust(l)
def rjust(s:str, l:int): return s.rjust(l)


# this code was taken from `textualize/rich` library because `textual` internal
# parser has a bug that incorrectly parses ANSI control characters
# Parsing is done via `rich.Text` class and the object is then fed in this
# function to parse ANSI codes without escaping `rich` markup
def markup(self) -> str:
    """Get console markup to render this Text.

    Returns:
        str: A string potentially creating markup tags.
    """

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