from typing import Literal
import libvirt
from colorama import Back, Fore, Style
from math import ceil, floor
from containers import BaseModule
from modules.resourceusage import createBar


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
    times = {}

    def __init__(self, *, domain: str = None,
                 resource_usage: "Literal['none', 'auto', 'onerow', 'tworow']" = 'auto',
                 **kwargs):
        super().__init__(**kwargs)
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

    def __post_init__(self):
        if self.resource_rows < 0:
            if self.content_size.width < 22:
                self.resource_rows = 2
            else:
                self.resource_rows = 1

    def dom_cpu_dict(self, dom: 'libvirt.virDomain'):
        return {
            'cpu_time': int(dom.getCPUStats(True)[0]['cpu_time']), 
            'vcpus': dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_LIVE)
        }

    def __call__(self):
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
                name[: self.content_size.width - max_len - 1].ljust(
                    self.content_size.width - max_len - 1
                )
                + " "
                + _color_state_map.get(state)
                + "\n"
            )
            
            if self.resource_rows > 0:
                cpu, ram = 0, 0
                if new_times.get(name) is None or self.times.get(name) is None:
                    # one or both new and old times are None,
                    # domain might have been just powered on or off
                    cpu = 0
                elif new_times[name]['vcpus'] != self.times[name]['vcpus']:
                    # guest vCPUs number has changed, old data is invalid
                    cpu = 0
                else:
                    cpu_delta = new_times[name]['cpu_time'] - self.times[name]['cpu_time']
                    cpu = cpu_delta*100/(1e9*new_times[name]['vcpus']*self.refreshInterval)
                    
                mem = memory.get(name, {'available': 1, 'unused': 1})
                # if the domain is powered off this will be (1-1/1)*100=0
                ram = (1-mem['unused']/mem['available'])*100
                
                if name in memory:
                    ram_txt = f'{sizeof_fmt(mem['available']-mem['unused'])}/{sizeof_fmt(mem['available'])}'
                else:
                    ram_txt = '0B'
                
                if self.resource_rows == 1:
                    libvirt_info += (
                        createBar(ceil(self.content_size.width/2), cpu, f'{cpu}%', 'CPU', 'red')
                        +
                        createBar(floor(self.content_size.width/2), ram, ram_txt, 'Mem', 'green')
                        + "\n"
                    )
                else:
                    libvirt_info += (
                        createBar(self.content_size.width, cpu, f'{cpu}%', 'CPU', 'red')
                        + "\n" +
                        createBar(self.content_size.width, ram, ram_txt, 'Mem', 'green')
                        + "\n"
                    )

        return libvirt_info


def sizeof_fmt(num, suffix="B"):
    # apparently libvirt memoryStat returns the results in kilobytes (power of 10)
    # so we need to adapt the function defined in helpers.units to properly convert values
    for unit in ("K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1000.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f}Y{suffix}"


widget = Libvirt
