from multisort import multisort
from requests import Session

base_url = "http://localhost:5002"

states_map = {
    'allocating':'A',
    'downloading':'D',
    'checkingDL':'CD',
    'forcedDL':'FD',
    'metaDL':'MD',
    'pausedDL':'PD',
    'queuedDL':'QD',
    'stalledDL':'SD',
    'error':'E',
    'missingFiles':'MF',
    'uploading':'U',
    'checkingUP':'CU',
    'forcedUP':'FU',
    'pausedUP':'PU',
    'queuedUP':'QU',
    'stalledUP':'SU',
    'queuedChecking': 'QC',
    'checkingResumeData':'CR',
    'moving':'MV',
    'unknown':'?'
}


class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"


colors_map = {
    "allocating": Colors.GREEN,
    "downloading": Colors.GREEN,
    "checkingDL": Colors.YELLOW,
    "forcedDL": Colors.CYAN,
    "metaDL": Colors.BLUE,
    "pausedDL": Colors.DARK_GRAY,
    "queuedDL": Colors.BLUE,
    "stalledDL": Colors.YELLOW,
    "error": Colors.RED,
    "missingFiles": Colors.RED,
    "uploading": Colors.GREEN,
    "checkingUP": Colors.YELLOW,
    "forcedUP": Colors.CYAN,
    "pausedUP": Colors.DARK_GRAY,
    "queuedUP": Colors.BLUE,
    "stalledUP": Colors.YELLOW,
    "queuedChecking": Colors.BLUE,
    "checkingResumeData": Colors.YELLOW,
    "moving": Colors.GREEN,
    "unknown": Colors.MAGENTA
}

s = Session()

login_response = s.post(base_url + '/api/v2/auth/login', data={"username": "admin", "password": "hplp2475w"}, headers={'Referer': base_url})

torrents = s.get(base_url + '/api/v2/torrents/info?filter=all&reverse=false&sort=downloaded').json()

for t in multisort(torrents, ['progress', 'ratio', 'name']):
    print("{}{:>2}{} {:3.0f}% {:3.0f}% {}".format(
        colors_map.get(t['state'], Colors.END), states_map.get(t['state'], '?'), Colors.END,
         t['progress']*100, t['ratio']*100, t['name']))
