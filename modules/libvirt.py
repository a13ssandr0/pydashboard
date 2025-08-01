from math import ceil, floor
from typing import Literal

import libvirt
from containers import BaseModule
from utils.bars import create_bar
from utils.types import Size
from utils.units import perc_fmt, sizeof_fmt

_state_map = {
    libvirt.VIR_DOMAIN_NOSTATE    : "nostate",
    libvirt.VIR_DOMAIN_RUNNING    : "running",
    libvirt.VIR_DOMAIN_BLOCKED    : "blocked",
    libvirt.VIR_DOMAIN_PAUSED     : "paused",
    libvirt.VIR_DOMAIN_SHUTDOWN   : "shutdown",
    libvirt.VIR_DOMAIN_SHUTOFF    : "shutoff",
    libvirt.VIR_DOMAIN_CRASHED    : "crashed",
    libvirt.VIR_DOMAIN_PMSUSPENDED: "pmsuspended",
}
_color_state_map = {
    "nostate"    : f"nostate",
    "running"    : f"[green]running[/green]",
    "blocked"    : f"[magenta]blocked[/magenta]",
    "paused"     : f"[yellow]paused[/yellow]",
    "shutdown"   : f"[red]shutdown[/red]",
    "shutoff"    : f"[red]shutoff[/red]",
    "crashed"    : f"[red]crashed[/red]",
    "pmsuspended": f"[yellow]pmsuspended[/yellow]",
    "unknown"    : f"[yellow]unknown[/yellow]",
}


class Libvirt(BaseModule):
    times = {}

    def __init__(self, *, domain: str = None,
                 resource_usage: "Literal['none', 'auto', 'onerow', 'tworow']" = 'auto',
                 **kwargs):
        super().__init__(domain=domain, resource_usage=resource_usage, **kwargs)
        self.domain = domain

        if resource_usage == 'none':
            self.resource_rows = 0
        elif resource_usage == 'auto':
            self.resource_rows = -1
        elif resource_usage == 'onerow':
            self.resource_rows = 1
        elif resource_usage == 'tworow':
            self.resource_rows = 2

        if self.resource_rows > 0:
            with libvirt.open(self.domain) as conn:
                self.times = {
                    dom.name(): self.dom_cpu_dict(dom)
                    for dom in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }

    def __post_init__(self, content_size: Size):
        if self.resource_rows < 0:
            if content_size[1] < 22:
                self.resource_rows = 2
            else:
                self.resource_rows = 1

    @staticmethod
    def dom_cpu_dict(dom: 'libvirt.virDomain'):
        return {
            'cpu_time': int(dom.getCPUStats(True)[0]['cpu_time']),
            'vcpus'   : dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_LIVE)
        }

    def __call__(self, content_size: Size):
        with libvirt.open(self.domain) as conn:
            states = [
                (dom.name(), _state_map.get(dom.state()[0], "unknown"))
                for dom in conn.listAllDomains()
            ]
            if self.resource_rows > 0:
                new_times = {
                    dom.name(): self.dom_cpu_dict(dom)
                    for dom in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }
                memory = {
                    dom.name(): dom.memoryStats()
                    for dom in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }

        states.sort(key=lambda x: x[0])
        max_len = 0
        for s in states:
            l = len(s[1])
            if l > max_len:
                max_len = l

        libvirt_info = ""
        for name, state in states:
            libvirt_info += (
                    name[: content_size[1] - max_len - 1].ljust(content_size[1] - max_len - 1)
                    + " "
                    + _color_state_map.get(state)
                    + "\n"
            )

            if self.resource_rows > 0:
                if new_times.get(name) is None or self.times.get(name) is None:
                    # one or both new and old times are None,
                    # domain might have been just powered on or off
                    cpu = 0
                elif new_times[name]['vcpus'] != self.times[name]['vcpus']:
                    # guest vCPUs number has changed, old data is invalid
                    cpu = 0
                else:
                    cpu_delta = new_times[name]['cpu_time'] - self.times[name]['cpu_time']
                    cpu = cpu_delta / (1e9 * new_times[name]['vcpus'] * self.refreshInterval)

                self.times = new_times

                mem = memory.get(name, {'available': 1, 'unused': 1})
                # if the domain is powered off this will be (1-1/1)*100=0
                ram = (1 - mem['unused'] / mem['available']) * 100

                if name in memory:
                    used = sizeof_fmt((mem['available'] - mem['unused']) * 1000.0, div=1000.0)
                    total = sizeof_fmt(mem['available'] * 1000.0, div=1000.0)
                    ram_txt = f"{used}/{total}"
                else:
                    ram_txt = '0B'

                if self.resource_rows == 1:
                    libvirt_info += (
                            create_bar(ceil(content_size[1] / 2), cpu * 100, perc_fmt(cpu), 'CPU', 'red')
                            +
                            create_bar(floor(content_size[1] / 2), ram, ram_txt, 'Mem', 'green')
                    )
                else:
                    libvirt_info += (
                            create_bar(content_size[1], cpu * 100, perc_fmt(cpu), 'CPU', 'red')
                            + "\n" +
                            create_bar(content_size[1], ram, ram_txt, 'Mem', 'green')
                    )

        return libvirt_info


widget = Libvirt
