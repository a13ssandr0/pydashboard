from typing import Any

import proxmoxer.core
from pandas import DataFrame
from proxmoxer import ProxmoxAPI

from pydashboard.containers import TableModule
from pydashboard.utils.units import perc_fmt, sizeof_fmt


def colorize_percentage(pct):
    _pct = pct
    if isinstance(_pct, str):
        if _pct and _pct.endswith('%'):
            _pct = float(_pct[:-1]) / 100.0
        else:
            return pct

    if _pct >= 0.9:
        return f'[red]{pct}[/red]'
    elif _pct >= 0.7:
        return f'[yellow]{pct}[/yellow]'
    else:
        return pct


_justify = {
    "active"       : "center",
    "avail"        : "right",
    "content"      : "left",
    "enabled"      : "center",
    "node"         : "left",
    "shared"       : "center",
    "storage"      : "left",
    "total"        : "right",
    "type"         : "left",
    "used"         : "right",
    "used_fraction": "right",
}

_human = {
    "active"       : lambda x: 'yes' if x else 'no',
    "avail"        : sizeof_fmt(),
    "content"      : lambda x: ','.join(sorted(x.split(','))),
    "enabled"      : lambda x: 'yes' if x else 'no',
    "shared"       : lambda x: 'yes' if x else 'no',
    "total"        : sizeof_fmt(),
    "used"         : sizeof_fmt(),
    "used_fraction": perc_fmt(100.0),
}

_names_map = {
    "active"       : "Active",
    "avail"        : "Available",
    "content"      : "Content",
    "enabled"      : "Enabled",
    "node"         : "Node",
    "shared"       : "Shared",
    "storage"      : "Storage",
    "total"        : "Total",
    "type"         : "Type",
    "used"         : "Used",
    "used_fraction": "Used%",
}


class ProxmoxStorage(TableModule):
    colorize = {'used_fraction': colorize_percentage}
    column_names = _names_map
    justify = _justify

    def __init__(self, *, token_name: str, token_secret: str,
                 host: str = "localhost", user: str = "root@pam", verify_ssl: bool = True,
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] = ('node', 'storage'),
                 columns: list[str] = ('node', 'storage', 'avail', 'used', 'used_fraction', 'total', 'type', 'content',
                                       'active', 'enabled', 'shared'),
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
                                  timeout=self.refresh_interval)

    def __call__(self):
        rows = []
        try:
            for node in self.proxmox.nodes.get():
                for storage in self.proxmox.nodes(node['node']).storage.get():
                    storage['node'] = node['node']
                    rows.append(storage)
            self.reset_settings('border_subtitle')
            self.reset_settings('styles.border_subtitle_color')
            return DataFrame.from_records(rows)

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


widget = ProxmoxStorage
