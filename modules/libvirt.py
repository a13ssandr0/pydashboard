import libvirt
from colorama import Back, Fore, Style

from containers import BaseModule

_state_map = {
    libvirt.VIR_DOMAIN_NOSTATE:     "nostate",
    libvirt.VIR_DOMAIN_RUNNING:     "running",
    libvirt.VIR_DOMAIN_BLOCKED:     "blocked",
    libvirt.VIR_DOMAIN_PAUSED:      "paused",
    libvirt.VIR_DOMAIN_SHUTDOWN:    "shutdown",
    libvirt.VIR_DOMAIN_SHUTOFF:     "shutoff",
    libvirt.VIR_DOMAIN_CRASHED:     "crashed",
    libvirt.VIR_DOMAIN_PMSUSPENDED: "pmsuspended",
}
_color_state_map = {
    "nostate":     f"{Fore.LIGHTWHITE_EX}nostate{Style.RESET_ALL}",
    "running":     f"{Fore.LIGHTGREEN_EX}running{Style.RESET_ALL}",
    "blocked":     f"{Fore.MAGENTA}blocked{Style.RESET_ALL}",
    "paused":      f"{Fore.LIGHTYELLOW_EX}paused{Style.RESET_ALL}",
    "shutdown":    f"{Fore.RED}shutdown{Style.RESET_ALL}",
    "shutoff":     f"{Fore.RED}shutoff{Style.RESET_ALL}",
    "crashed":     f"{Back.RED}crashed{Style.RESET_ALL}",
    "pmsuspended": f"{Fore.LIGHTYELLOW_EX}pmsuspended{Style.RESET_ALL}",
    "unknown":     f"{Fore.LIGHTYELLOW_EX}unknown{Style.RESET_ALL}",
}


class Libvirt(BaseModule):

    def __init__(self, *, domain: str = None, **kwargs):
        super().__init__(**kwargs)
        self.domain = domain

    def __call__(self):
        with libvirt.open(self.domain) as conn:
            states = [
                (dom.name(), _state_map.get(dom.state()[0], "unknown"))
                for dom in conn.listAllDomains()
            ]

        states.sort(key=lambda x: x[0])
        max_len = 0
        for s in states:
            l = len(s[1])
            if l > max_len:
                max_len = l

        libvirt_info = ""
        for dom in states:
            libvirt_info += (
                dom[0][: self.content_size.width - max_len - 1].ljust(
                    self.content_size.width - max_len - 1
                )
                + " "
                + _color_state_map.get(dom[1])
                + "\n"
            )

        return libvirt_info


widget = Libvirt
