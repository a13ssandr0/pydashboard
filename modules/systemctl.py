import re
from os.path import splitext
from subprocess import run

from colorama import Fore, Style

from containers import BaseModule

# _whites = [
#     "alias",
#     "auto-restart",
#     "condition",
#     "disabled",
#     "elapsed",
#     "exited",
#     "final-sigkill",
#     "final-sigterm",
#     "final-watchdog",
#     "inactive",
#     "indirect",
#     "linked",
#     "linked-runtime",
#     "stub",
#     "tentative",
#     "transient",
# ]
_greens = [
    "activating-done",
    "active",
    "enabled",
    "enabled-runtime",
    "generated",
    "listening",
    "loaded",
    "merged",
    "mounted",
    "mounting-done",
    "plugged",
    "running",
]
_yellows = [
    "activating",
    "auto-restart-queued",
    "cleaning",
    "deactivating-sigkill",
    "deactivating-sigterm",
    "deactivating",
    "maintenance",
    "masked-runtime",
    "masked",
    "mounting",
    "reload-notify",
    "reload-signal",
    "reload",
    "reloading",
    "remounting-sigkill",
    "remounting-sigterm",
    "remounting",
    "start-chown",
    "start-post",
    "start-pre",
    "start",
    "static",
    "stop-post",
    "stop-pre-sigkill",
    "stop-pre-sigterm",
    "stop-pre",
    "stop-sigkill",
    "stop-sigterm",
    "stop-watchdog",
    "stop",
    "unmounting-sigkill",
    "unmounting-sigterm",
    "unmounting",
    "waiting",
]
_reds = [
    "abandoned",
    "bad",
    "bad-setting",
    "dead",
    "dead-before-auto-restart",
    "dead-resources-pinned",
    "error",
    "failed",
    "failed-before-auto-restart",
    "not-found",
]


def sysctl_states_map(status):
    if status in _greens:
        return f"{Fore.LIGHTGREEN_EX}{status}{Style.RESET_ALL}"
    elif status in _yellows:
        return f"{Fore.LIGHTYELLOW_EX}{status}{Style.RESET_ALL}"
    elif status in _reds:
        return f"{Fore.RED}{status}{Style.RESET_ALL}"
    else:
        return status




class Systemctl(BaseModule):

    def __init__(self, *, units: list[str] = [], **kwargs):
        super().__init__(**kwargs)
        self.units = units

    def __call__(self):
        my_units = run(
            ["systemctl", "list-units", "--failed", "--quiet", "--plain"],
            capture_output=True, text=True
        ).stdout
        if self.units:
            my_units += run(
                ["systemctl", "list-units", "--all", "--quiet", "--plain", *self.units],
                capture_output=True, text=True
            ).stdout

        my_units = [
            u.split(" ", 4) for u in re.sub("  *", " ", my_units).strip().split("\n") if u
        ]
        my_units = [(splitext(u[0])[0], u[3]) for u in my_units]
        max_len = 0
        for u in my_units:
            l = len(u[1])
            if l > max_len:
                max_len = l

        sysctl_info = ""
        seen_units = []
        for u in my_units:
            if u[0] not in seen_units:
                sysctl_info += (
                    u[0][: self.content_size.width - max_len - 1].ljust(self.content_size.width - max_len - 1)
                    + " "
                    + sysctl_states_map(u[1])
                    + "\n"
                )
                seen_units.append(u[0])

        return sysctl_info


widget = Systemctl
