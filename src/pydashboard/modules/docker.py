from requests.exceptions import ConnectionError
from requests_unixsocket import get

from pydashboard.containers import BaseModule
from pydashboard.utils.types import Size
from pydashboard.utils.units import sizeof_fmt

_color_state = {
    "created"   : "[green]created[/green]",
    "restarting": "[yellow]restarting[/yellow]",
    "running"   : "[green]running[/green]",
    "removing"  : "[yellow]removing[/yellow]",
    "paused"    : "[yellow]paused[/yellow]",
    "exited"    : "[red]exited[/red]",
    "dead"      : "[red]dead[/red]",
}


class Docker(BaseModule):
    """
    Docker module has no specific configuration parameters, see [BaseModule](../containers/basemodule.md).

    !!! warning
        This module needs the user to be in the `docker` group to get sufficient permissions to connect to docker.
        If not present yet, the `docker` group has to be created.
        ```bash
        sudo addgroup docker
        sudo adduser $(whoami) docker
        ```

        It's totally fine if the above command produce the following outputs:
        ``` title="sudo addgroup docker"
        fatal: The group `docker' already exists.
        ```
        ``` title="sudo adduser $(whoami) docker"
        info: The user `alessandro' is already a member of `docker'.
        ```
    """

    def __call__(self, size: Size):
        try:
            sys_info = get('http+unix://%2Fvar%2Frun%2Fdocker.sock/info').json()
            sys_df = get('http+unix://%2Fvar%2Frun%2Fdocker.sock/system/df').json()
            vol_info = get('http+unix://%2Fvar%2Frun%2Fdocker.sock/volumes').json()
            ctr_info = get('http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/json?all=true').json()

            max_len = 0
            for ctr in ctr_info:
                ctr['Names'] = ctr['Names'][0].split('/')[-1]
                l = len(ctr["State"])
                if l > max_len:
                    max_len = l
            ctr_info.sort(key=lambda x: x["Names"])

            cont_spc = sizeof_fmt(sum([c.get("SizeRw", 0) for c in sys_df['Containers']]), div=1000.0)
            imgs_spc = sizeof_fmt(sum([c.get("Size", 0) for c in sys_df['Images']]), div=1000.0)
            vols_spc = sizeof_fmt(sum([c.get("UsageData", {}).get("Size", 0) for c in sys_df['Volumes']]), div=1000.0)

            return (
                """Containers: {cont:>3}   Running: [green]{runn:>3}[/green]\n"""
                """ Images:    {imgs:>3}   Paused:  [yellow]{paus:>3}[/yellow]\n"""
                """ Volumes:   {vols:>3}   Stopped: [red]{stop:>3}[/red]\n"""
                """Disk usage:       Containers: {cont_spc}\n"""
                """ Images: {imgs_spc:<8} Volumes:    {vols_spc}\n"""
            ).format_map(
                    dict(
                            cont=sys_info["Containers"],
                            runn=sys_info["ContainersRunning"],
                            imgs=sys_info["Images"],
                            paus=sys_info["ContainersPaused"],
                            vols=len(vol_info),
                            stop=sys_info["ContainersStopped"],
                            cont_spc=cont_spc,
                            imgs_spc=imgs_spc,
                            vols_spc=vols_spc,
                    )
            ) + "\n".join(
                    [
                        f"{c['Names'][:size[1] - max_len - 1].ljust(size[1] - max_len - 1)} {_color_state.get(c['State'], c['State'])}"
                        for c in ctr_info
                    ]
            )
        except FileNotFoundError:
            self.logger.error('Cannot connect to Docker')
            return "[yellow]Docker not installed[/yellow]"
        except (ConnectionError, PermissionError) as e:
            self.logger.error('Docker connection error: {}', e)
            return f"[red]{e}[/red]"

widget = Docker
