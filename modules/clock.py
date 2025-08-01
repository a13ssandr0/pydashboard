from datetime import datetime

from containers import BaseModule


# noinspection PyPep8Naming
class Clock(BaseModule):
    # noinspection PyShadowingBuiltins
    def __init__(self, *, font: str = 'bigFont', format: str = None, compact=False, showSeconds=False, **kwargs):
        super().__init__(font=font, format=format, compact=compact, showSeconds=showSeconds, **kwargs)
        self.font = fonts.get(font, fonts['bigFont'])
        self.format = format
        self.compact = compact
        self.bf1 = "%H:%M:%S" if showSeconds else "%H:%M"
        self.bf2 = "%H %M %S" if showSeconds else "%H %M"

    def __call__(self):
        now = datetime.now()
        time_str = join_font(self.font, now.strftime(self.bf1 if now.second % 2 else self.bf2), self.compact)
        if self.format:
            time_str += now.strftime(self.format)
        return time_str


widget = Clock


def join_font(font: dict[str, list[str]], string: str, compact: bool):
    spc = "" if compact else " "
    rows = len(font['1'])
    out = ""
    for r in range(rows):
        for c in string:
            out += spc + font[c][r]
        out += '\n'
    return out


fonts = {
    'digitalFont': {
        "1": ["▄█ ", " █ ", "▄█▄"],
        "2": ["█▀█", " ▄▀", "█▄▄"],
        "3": ["█▀▀█", "  ▀▄", "█▄▄█"],
        "4": [" █▀█ ", "█▄▄█▄", "   █ "],
        "5": ["█▀▀", "▀▀▄", "▄▄▀"],
        "6": ["▄▀▀▄", "█▄▄ ", "▀▄▄▀"],
        "7": ["▀▀▀█", "  █ ", " ▐▌ "],
        "8": ["▄▀▀▄", "▄▀▀▄", "▀▄▄▀"],
        "9": ["▄▀▀▄", "▀▄▄█", " ▄▄▀"],
        "0": ["█▀▀█", "█  █", "█▄▄█"],
        ":": ["█", " ", "█"],
        " ": [" ", " ", " "],
        "A": ["", "", "AM"],
        "P": ["", "", "PM"],
    },

    'bigFont'    : {
        "1": [" ┏┓ ", "┏┛┃ ", "┗┓┃ ", " ┃┃ ", "┏┛┗┓", "┗━━┛"],
        "2": ["┏━━━┓", "┃┏━┓┃", "┗┛┏┛┃", "┏━┛┏┛", "┃ ┗━┓", "┗━━━┛"],
        "3": ["┏━━━┓", "┃┏━┓┃", "┗┛┏┛┃", "┏┓┗┓┃", "┃┗━┛┃", "┗━━━┛"],
        "4": ["┏┓ ┏┓", "┃┃ ┃┃", "┃┗━┛┃", "┗━━┓┃", "   ┃┃", "   ┗┛"],
        "5": ["┏━━━┓", "┃┏━━┛", "┃┗━━┓", "┗━━┓┃", "┏━━┛┃", "┗━━━┛"],
        "6": ["┏━━━┓", "┃┏━━┛", "┃┗━━┓", "┃┏━┓┃", "┃┗━┛┃", "┗━━━┛"],
        "7": ["┏━━━┓", "┃┏━┓┃", "┗┛┏┛┃", "  ┃┏┛", "  ┃┃ ", "  ┗┛ "],
        "8": ["┏━━━┓", "┃┏━┓┃", "┃┗━┛┃", "┃┏━┓┃", "┃┗━┛┃", "┗━━━┛"],
        "9": ["┏━━━┓", "┃┏━┓┃", "┃┗━┛┃", "┗━━┓┃", "┏━━┛┃", "┗━━━┛"],
        "0": ["┏━━━┓", "┃┏━┓┃", "┃┃ ┃┃", "┃┃ ┃┃", "┃┗━┛┃", "┗━━━┛"],
        ":": ["   ", "┏━┓", "┗━┛", "┏━┓", "┗━┛", "   "],
        " ": ["   ", "   ", "   ", "   ", "   ", "   "],
        "A": ["", "", "", "", "", "AM"],
        "P": ["", "", "", "", "", "PM"],
    },

    'boldFont'   : {
        "1": ["██", "██", "██", "██", "██"],
        "2": ["██████", "    ██", "██████", "██    ", "██████"],
        "3": ["██████", "    ██", "██████", "    ██", "██████"],
        "4": ["██  ██", "██  ██", "██████", "    ██", "    ██"],
        "5": ["██████", "██    ", "██████", "    ██", "██████"],
        "6": ["██████", "██    ", "██████", "██  ██", "██████"],
        "7": ["██████", "    ██", "    ██", "    ██", "    ██"],
        "8": ["██████", "██  ██", "██████", "██  ██", "██████"],
        "9": ["██████", "██  ██", "██████", "    ██", "██████"],
        "0": ["██████", "██  ██", "██  ██", "██  ██", "██████"],
        ":": ["  ", "██", "  ", "██", "  "],
        " ": ["  ", "  ", "  ", "  ", "  "],
        "A": ["", "", "", "", "AM"],
        "P": ["", "", "", "", "PM"],
    },
}
