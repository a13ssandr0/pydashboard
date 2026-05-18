from typing import Any

import proxmoxer.core
from pandas import DataFrame
from proxmoxer import ProxmoxAPI

from pydashboard.containers import TableModule
from pydashboard.utils.units import duration_fmt, perc_fmt, sizeof_fmt, speedof_fmt

colors_map = {
    "unknown": "yellow",
    "offline": "red",
    "stopped": "red",
    "online" : "green",
    "running": "green",
}


def colorize(state):
    c = colors_map.get(state, colors_map['unknown'])
    return f'[{c}]{state}[/{c}]'


def colorize_percentage(pct):
    _pct = pct
    if isinstance(_pct, str):
        if not _pct: return _pct
        _pct = float(_pct[:-1])

    if _pct >= 90:
        return f'[red]{pct}[/red]'
    elif _pct >= 70:
        return f'[yellow]{pct}[/yellow]'
    else:
        return pct


_justify = {
    "combined_name"     : "left",
    "cpu"               : "right",
    "cpus"              : "center",
    "disk"              : "right",
    "diskpct"           : "right",
    "diskread"          : "right",
    "diskwrite"         : "right",
    "id"                : "right",
    "level"             : "left",
    "maxcpu"            : "center",
    "maxdisk"           : "right",
    "maxmem"            : "right",
    "mempct"            : "right",
    "maxswap"           : "right",
    "mem"               : "right",
    "memhost"           : "right",
    "name"              : "left",
    "netin"             : "right",
    "netout"            : "right",
    "node"              : "left",
    "pid"               : "right",
    "pressurecpufull"   : "right",
    "pressurecpusome"   : "right",
    "pressureiofull"    : "right",
    "pressureiosome"    : "right",
    "pressurememoryfull": "right",
    "pressurememorysome": "right",
    "ssl_fingerprint"   : "left",
    "status"            : "left",
    "swap"              : "right",
    "swappct"           : "right",
    "type"              : "left",
    "uptime"            : "right",
    "vmid"              : "right"
}

_human = {
    "cpu"      : perc_fmt(100.0),
    "disk"     : sizeof_fmt(),
    "diskread" : speedof_fmt(),
    "diskpct"  : perc_fmt(100.0),
    "diskwrite": speedof_fmt(),
    "maxdisk"  : sizeof_fmt(),
    "maxmem"   : sizeof_fmt(),
    "maxswap"  : sizeof_fmt(),
    "mem"      : sizeof_fmt(),
    "memhost"  : sizeof_fmt(),
    "mempct"   : perc_fmt(100.0),
    "netin"    : speedof_fmt(),
    "netout"   : speedof_fmt(),
    "swap"     : sizeof_fmt(),
    "swappct"  : perc_fmt(100.0),
    "uptime"   : lambda x: duration_fmt(x) if x > 0 else '',
    "vmid"     : lambda x: x if x >= 0 else '',
}

_names_map = {
    "combined_name"     : "Name",
    "cpu"               : "CPU%",
    "cpus"              : "CPUs",
    "disk"              : "Disk",
    "diskpct"           : "Disk%",
    "diskread"          : "Disk Read",
    "diskwrite"         : "Disk Write",
    "id"                : "ID",
    "level"             : "Level",
    "maxcpu"            : "Max CPU",
    "maxdisk"           : "Max Disk",
    "maxmem"            : "Max Mem",
    "mempct"            : "Mem%",
    "maxswap"           : "Max Swap",
    "mem"               : "Mem",
    "memhost"           : "Host Mem",
    "name"              : "Name",
    "netin"             : "Network in",
    "netout"            : "Network out",
    "node"              : "Node",
    "pid"               : "PID",
    "pressurecpufull"   : "Pressure CPU full",
    "pressurecpusome"   : "Pressure CPU some",
    "pressureiofull"    : "Pressure IO full",
    "pressureiosome"    : "Pressure IO some",
    "pressurememoryfull": "Pressure Mem full",
    "pressurememorysome": "Pressure Mem some",
    "ssl_fingerprint"   : "SSL fingerprint",
    "status"            : "Status",
    "swap"              : "Swap",
    "swappct"           : "Swap%",
    "type"              : "Type",
    "uptime"            : "Uptime",
    "vmid"              : "VM ID"
}


def normalize_records(records: list[dict]) -> list[dict]:
    all_keys = {k for record in records for k in record}

    normalized = []
    for record in records:
        new_record = {}
        for key in all_keys:
            value = record.get(key)
            if isinstance(value, str):
                new_record[key] = value
            elif isinstance(value, int):
                new_record[key] = value
            elif isinstance(value, float):
                new_record[key] = value
            else:
                new_record[key] = ""
        normalized.append(new_record)

    return normalized


def records_to_df(records: list[dict]) -> DataFrame:
    normalized = normalize_records(records)
    df = DataFrame.from_records(normalized)

    # Per ogni colonna, se contiene misti (int/""), usa object dtype
    # altrimenti pandas può fare inferenza corretta
    for col in df.columns:
        sample = next((v for v in df[col] if v != ""), None)
        if isinstance(sample, int):
            df[col] = df[col].astype(object)

    return df


class Proxmox(TableModule):
    colorize = {'status': colorize, 'mempct': colorize_percentage, 'diskpct': colorize_percentage,
                'cpu'   : colorize_percentage}
    column_names = _names_map
    justify = _justify

    def __init__(self, *, token_name: str, token_secret: str,
                 host: str = "localhost", user: str = "root@pam", verify_ssl: bool = True,
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] = ('node', 'vmid'),
                 columns: list[str] = ('combined_name', 'status', 'uptime',
                                       'cpu', 'cpus',
                                       'mem', 'mempct', 'maxmem',
                                       'swap', 'swappct', 'maxswap',
                                       'disk', 'diskpct', 'maxdisk'),
                 human_readable: bool = True, **kwargs: Any):
        """
        Proxmox VM and container status.
        By default, are sorted by node and for each node VMs and Containers are sorted by id.

        Args:
            host: Proxmox host IP
            user: Proxmox user (<user\>@<realm\>)
            token_name: Proxmox token name
            token_secret: Proxmox token secret
            verify_ssl: Whether to check SSL certificate validity
            **kwargs: See [TableModule](../containers/tablemodule.md)

        # Available columns
        Source and attribute meaning: [PVE Docs: Nodes](https://pve.proxmox.com/pve-docs/api-viewer/#/nodes)
        Attributes with `*` are not part of the official API or its behavior is slightly different.
        Note: According to Proxmox API documentation, some optional attributes are not always present and might not
        be included in the table below. Open a [new issue](https://github.com/a13ssandr0/pydashboard/issues/new/choose)
        if you find an attribute you need is missing or add it yourself and submit a new pull request.

        Attribute              | node |  vm  |  lxc | Notes
        -----------------------|------|------|------|---------
        `combined_name`*       |  ✅  |  ✅  |  ✅  | Node and VM/Container names in a single column like in web UI.
        `cpu`                  |  ✅  |  ✅  |  ✅  |
        `cpus`                 |  ✅* |  ✅  |  ✅  | * same as `maxcpu`
        `maxcpu`               |  ✅  |  ✅* |  ✅* | * same as `cpus`
        `disk`                 |  ✅  |  ✅  |  ✅  |
        `diskpct`*             |  ✅  |  ✅  |  ✅  | `disk/maxdisk`
        `diskread`             |      |      |  ✅  |
        `diskwrite`            |      |      |  ✅  |
        `id`                   |  ✅  |      |      |
        `vmid`                 |  ✅* |  ✅  |  ✅  | * For nodes is equal to `-1` and hidden, is used only for sorting.
        `level`                |  ✅  |      |      |
        `maxdisk`              |  ✅  |  ✅  |  ✅  |
        `maxmem`               |  ✅  |  ✅  |  ✅  |
        `maxswap`              |      |      |  ✅  |
        `mem`                  |  ✅  |  ✅  |  ✅  |
        `mempct`*              |  ✅  |  ✅  |  ✅  | `mem/maxmem`
        `memhost`              |      |  ✅  |      |
        `name`                 |      |  ✅  |  ✅  |
        `node`                 |  ✅  |  ✅* |  ✅* | * For VMs and Containers is arbitrarily copied from parent node.
        `netin`                |      |  ✅  |  ✅  |
        `netout`               |      |  ✅  |  ✅  |
        `pid`                  |      |  ✅  |  ✅  |
        `pressurecpufull`      |      |  ✅  |  ✅  |
        `pressurecpusome`      |      |  ✅  |  ✅  |
        `pressureiofull`       |      |  ✅  |  ✅  |
        `pressureiosome`       |      |  ✅  |  ✅  |
        `pressurememoryfull`   |      |  ✅  |  ✅  |
        `pressurememorysome`   |      |  ✅  |  ✅  |
        `ssl_fingerprint`      |  ✅  |      |      |
        `status`               |  ✅  |  ✅  |  ✅  |
        `swap`                 |      |      |  ✅  |
        `swappct`              |      |      |  ✅* | `swap/maxswap`
        `type`                 |  ✅  |      |  ✅  |
        `uptime`               |  ✅  |  ✅  |  ✅  |

        """
        super().__init__(host=host, user=user, token_name=token_name, token_secret=token_secret, verify_ssl=verify_ssl,
                         sort=sort, columns=columns, human_readable=human_readable, **kwargs)
        self.host = host
        self.user = user
        self.token_name = token_name
        self.token_secret = token_secret
        self.verify_ssl = verify_ssl
        self.humanize = _human if human_readable else None

    def __post_init__(self):
        self.proxmox = ProxmoxAPI(host=self.host, user=self.user, token_name=self.token_name,
                                  token_value=self.token_secret, verify_ssl=self.verify_ssl,
                                  timeout=max(self.refresh_interval-1, 0))

    def __call__(self):
        rows = []
        try:
            for node in self.proxmox.nodes.get():
                # Probably not the best way, but allows to sort hosts and vms having each host together with its vms
                node['vmid'] = -1
                node['combined_name'] = node['node']
                node['cpus'] = node['maxcpu']
                node['mempct'] = node['mem'] / node['maxmem']
                try:
                    node['diskpct'] = node['disk'] / node['maxdisk']
                except ZeroDivisionError:
                    pass
                rows.append(node)

                _node = self.proxmox.nodes(node['node'])
                for hv in [_node.lxc, _node.qemu]:
                    for vm in hv.get():
                        vm['node'] = node['node']
                        vm['combined_name'] = f"{vm['vmid']} ({vm['name']})"
                        vm['maxcpu'] = vm['cpus']
                        vm['mempct'] = vm['mem'] / vm['maxmem']
                        try:
                            vm['diskpct'] = vm['disk'] / vm['maxdisk']
                        except ZeroDivisionError:
                            pass

                        try:
                            vm['swappct'] = vm['swap'] / vm['maxswap']
                        except (ZeroDivisionError, KeyError):
                            pass
                        rows.append(vm)
            self.reset_settings('border_subtitle')
            self.reset_settings('styles.border_subtitle_color')
            return records_to_df(rows)

        except proxmoxer.core.ResourceException as e:
            self.border_subtitle = f"{e.status_code} {e.status_message}: {e.content}".strip()
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))

        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))

        except TimeoutError:
            self.logger.error('TimeoutError')


widget = Proxmox
