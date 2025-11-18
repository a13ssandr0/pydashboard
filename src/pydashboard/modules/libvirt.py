import os
from math import ceil, floor
from typing import Any, Literal

if '__PYD_SKIP_OPTIONAL_IMPORTS__' not in os.environ:
    try:
        # noinspection PyUnresolvedReferences
        from libvirt import VIR_CONNECT_LIST_DOMAINS_ACTIVE, VIR_DOMAIN_AFFECT_LIVE, VIR_DOMAIN_BLOCKED, VIR_DOMAIN_CRASHED, \
            VIR_DOMAIN_NOSTATE, VIR_DOMAIN_PAUSED, VIR_DOMAIN_PMSUSPENDED, VIR_DOMAIN_RUNNING, VIR_DOMAIN_SHUTDOWN, \
            VIR_DOMAIN_SHUTOFF, openReadOnly, virDomain

        _state_map = {
            VIR_DOMAIN_NOSTATE    : "nostate",
            VIR_DOMAIN_RUNNING    : "running",
            VIR_DOMAIN_BLOCKED    : "blocked",
            VIR_DOMAIN_PAUSED     : "paused",
            VIR_DOMAIN_SHUTDOWN   : "shutdown",
            VIR_DOMAIN_SHUTOFF    : "shutoff",
            VIR_DOMAIN_CRASHED    : "crashed",
            VIR_DOMAIN_PMSUSPENDED: "pmsuspended",
        }
    except ImportError:
        raise ImportError("libvirt module is not available: you need to install 'pydashboard[libvirt]' to use this module.")
else:
    _state_map = {}

from pydashboard.containers import BaseModule
from pydashboard.utils.bars import create_bar
from pydashboard.utils.types import Size
from pydashboard.utils.units import perc_fmt, sizeof_fmt

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

    def __init__(self, *, hypervisor_uri: str = 'qemu:///system',
                 resource_usage: Literal['none', 'auto', 'onerow', 'tworow'] = 'auto',
                 **kwargs: Any):
        """
        !!! warning
            This module requires module `libvirt` to be installed. As this requires an external dependency, it must be
            installed explicitly after installing the missing dependency. See [Installation](../getting_started.md/#libvirt).

        Args:
            hypervisor_uri: [Local](https://libvirt.org/uri.html#local-hypervisor-uris) or
                            [Remote](https://libvirt.org/uri.html#remote-uris) hypervisor URIs
            resource_usage: CPU and RAM usage bars style
            **kwargs: See [BaseModule](../containers/basemodule.md)

        !!! warning
            This module needs the user to be in the `libvirt` group to get sufficient permissions to connect to libvirt.
            If not present yet, the `libvirt` group has to be created.
            ```bash
            sudo addgroup libvirt
            sudo adduser $(whoami) libvirt
            ```

            It's totally fine if the above command produce the following outputs:
            ``` title="sudo addgroup libvirt"
            fatal: The group `libvirt' already exists.
            ```
            ``` title="sudo adduser $(whoami) libvirt"
            info: The user `alessandro' is already a member of `libvirt'.
            ```
        """
        super().__init__(hypervisor_uri=hypervisor_uri, resource_usage=resource_usage, **kwargs)
        self.hypervisor_uri = hypervisor_uri

        if resource_usage == 'none':
            self.resource_rows = 0
        elif resource_usage == 'auto':
            self.resource_rows = -1
        elif resource_usage == 'onerow':
            self.resource_rows = 1
        elif resource_usage == 'tworow':
            self.resource_rows = 2

    def __post_init__(self, content_size: Size):
        if self.resource_rows != 0:
            with openReadOnly(self.hypervisor_uri) as conn:
                self.times = {
                    dom.name(): self.dom_cpu_dict(dom)
                    for dom in conn.listAllDomains(VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }

        if self.resource_rows < 0:
            if content_size[1] < 22:
                self.resource_rows = 2
            else:
                self.resource_rows = 1

    @staticmethod
    def dom_cpu_dict(dom: 'virDomain'):
        return {
            'cpu_time': int(dom.getCPUStats(True)[0]['cpu_time']),
            'vcpus'   : dom.vcpusFlags(VIR_DOMAIN_AFFECT_LIVE)
        }

    def __call__(self, content_size: Size):
        with openReadOnly(self.hypervisor_uri) as conn:
            states = [
                (dom.name(), _state_map.get(dom.state()[0], "unknown"))
                for dom in conn.listAllDomains()
            ]
            if self.resource_rows > 0:
                new_times = {
                    dom.name(): self.dom_cpu_dict(dom)
                    for dom in conn.listAllDomains(VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }
                memory = {
                    dom.name(): dom.memoryStats()
                    for dom in conn.listAllDomains(VIR_CONNECT_LIST_DOMAINS_ACTIVE)
                }

        states.sort(key=lambda x: x[0])
        max_len = 0
        for s in states:
            l = len(s[1])
            if l > max_len:
                max_len = l

        libvirt_info = ""
        for name, state in states:
            if libvirt_info:
                libvirt_info += "\n"
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
                    cpu = cpu_delta / (1e9 * new_times[name]['vcpus'] * self.refresh_interval)

                self.times = new_times

                mem = memory.get(name, {})
                # if the domain is powered off this will be (1-1/1)*100=0
                unused, available = mem.get('unused', 1), mem.get('available', 1)
                ram = (1 - unused / available) * 100

                if name in memory:
                    used = sizeof_fmt((available - unused) * 1000.0, div=1000.0)
                    total = sizeof_fmt(available * 1000.0, div=1000.0)
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
