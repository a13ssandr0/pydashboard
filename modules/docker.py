import json
from subprocess import run

from colorama import Fore, Style

from containers import BaseModule

_color_state = {
    "created": f"{Fore.GREEN}created{Style.RESET_ALL}",
    "restarting": f"{Fore.LIGHTYELLOW_EX}restarting{Style.RESET_ALL}",
    "running": f"{Fore.LIGHTGREEN_EX}running{Style.RESET_ALL}",
    "removing": f"{Fore.LIGHTYELLOW_EX}removing{Style.RESET_ALL}",
    "paused": f"{Fore.LIGHTYELLOW_EX}paused{Style.RESET_ALL}",
    "exited": f"{Fore.RED}exited{Style.RESET_ALL}",
    "dead": f"{Fore.RED}dead{Style.RESET_ALL}",
}


def _make_valid_json(s: str) -> str:
    return "[" + s.strip().replace("}\n", "},\n") + "]"


class Docker(BaseModule):

    def __call__(self):
        # out = '[red]Docker containers:[/red]' + '\n'
        try:
            sys_info = run(
                ["docker", "system", "info", "--format", "json"],
                capture_output=True,
                text=True,
            ).stdout
            sys_df = run(
                ["docker", "system", "df", "--format", "json"],
                capture_output=True,
                text=True,
            ).stdout
            vol_info = run(
                ["docker", "volume", "ls", "--format", "json"],
                capture_output=True,
                text=True,
            ).stdout
            ctr_info = run(
                ["docker", "container", "ls", "-a", "--format", "json"],
                capture_output=True,
                text=True,
            ).stdout

            sys_info = json.loads(sys_info)
            sys_df = {df["Type"]: df for df in json.loads(_make_valid_json(sys_df))}
            vol_info = json.loads(_make_valid_json(vol_info))
            ctr_info: list = json.loads(_make_valid_json(ctr_info))

            ctr_info.sort(key=lambda x: x["Names"])
            max_len = 0
            for ctr in ctr_info:
                l = len(ctr["State"])
                if l > max_len:
                    max_len = l

            return (
                """Containers: {cont:>3}   Running: {grn}{runn:>3}{reset}\n"""
                """ Images:    {imgs:>3}   Paused:  {ylw}{paus:>3}{reset}\n"""
                """ Volumes:   {vols:>3}   Stopped: {red}{stop:>3}{reset}\n"""
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
                    cont_spc=sys_df["Containers"]["Size"],
                    imgs_spc=sys_df["Images"]["Size"],
                    vols_spc=sys_df["Local Volumes"]["Size"],
                    grn=Fore.GREEN,
                    ylw=Fore.LIGHTYELLOW_EX,
                    red=Fore.RED,
                    reset=Style.RESET_ALL,
                )
            ) + "\n".join(
                [
                    f"{c['Names'][:self.content_size.width-max_len-1].ljust(self.content_size.width-max_len-1)} {_color_state.get(c['State'], c['State'])}"
                    for c in ctr_info
                ]
            )
        except FileNotFoundError:
            return "[yellow]Docker not installed[/yellow]"


widget = Docker
