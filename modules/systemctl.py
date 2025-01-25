import json
import re
import subprocess
from os.path import splitext

import libvirt
from colorama import Back, Fore, Style

from basemod import BaseModule


def do_docker(width:int):
    sys_info = subprocess.run(['docker', 'system', 'info', '--format', 'json'], stdout=subprocess.PIPE).stdout
    sys_df   = subprocess.run(['docker', 'system', 'df', '--format', 'json'], stdout=subprocess.PIPE).stdout
    vol_info = subprocess.run(['docker', 'volume', 'ls', '--format', 'json'], stdout=subprocess.PIPE).stdout
    ctr_info = subprocess.run(['docker', 'container', 'ls', '-a', '--format', 'json'], stdout=subprocess.PIPE).stdout

    sys_info = json.loads(sys_info)
    sys_df   = {df['Type']:df for df in json.loads('[' + sys_df.decode().strip().replace('}\n','},\n') + ']')}
    vol_info = json.loads('[' + vol_info.decode().strip().replace('}\n','},\n') + ']')
    ctr_info:list = json.loads('[' + ctr_info.decode().strip().replace('}\n','},\n') + ']')

    ctr_info.sort(key = lambda x: x['Names'])
    max_len = 0
    for ctr in ctr_info:
        l = len(ctr['State'])
        if l>max_len: max_len=l

    color_state = {
        'created':    f'{Fore.GREEN}created{Style.RESET_ALL}',    
        'restarting': f'{Fore.LIGHTYELLOW_EX}restarting{Style.RESET_ALL}', 
        'running':    f'{Fore.LIGHTGREEN_EX}running{Style.RESET_ALL}',    
        'removing':   f'{Fore.LIGHTYELLOW_EX}removing{Style.RESET_ALL}',   
        'paused':     f'{Fore.LIGHTYELLOW_EX}paused{Style.RESET_ALL}',     
        'exited':     f'{Fore.RED}exited{Style.RESET_ALL}',     
        'dead':       f'{Fore.RED}dead{Style.RESET_ALL}',       
    }


    docker_info = (
        '''Containers: {cont:>3}   Running: {grn}{runn:>3}{reset}\n'''
        ''' Images:    {imgs:>3}   Paused:  {ylw}{paus:>3}{reset}\n'''
        ''' Volumes:   {vols:>3}   Stopped: {red}{stop:>3}{reset}\n'''
        '''Disk usage:       Containers: {cont_spc}\n'''
        ''' Images: {imgs_spc:<8} Volumes:    {vols_spc}\n'''
    ).format_map(dict(
        cont=sys_info['Containers'], runn=sys_info['ContainersRunning'],
        imgs=sys_info['Images'],     paus=sys_info['ContainersPaused'],
        vols=len(vol_info),          stop=sys_info['ContainersStopped'],
        cont_spc=sys_df['Containers']['Size'], imgs_spc=sys_df['Images']['Size'],
        vols_spc=sys_df['Local Volumes']['Size'],
        grn=Fore.GREEN, ylw=Fore.LIGHTYELLOW_EX, red=Fore.RED, reset=Style.RESET_ALL
    )) + \
    '\n'.join([f'{c['Names'][:width-max_len-1].ljust(width-max_len-1)} {color_state.get(c['State'], c['State'])}' for c in ctr_info])

    return docker_info


def do_libvirt(width:int, hypervisor:str):
    state_map = {
        libvirt.VIR_DOMAIN_NOSTATE:     'nostate',
        libvirt.VIR_DOMAIN_RUNNING:     'running',
        libvirt.VIR_DOMAIN_BLOCKED:     'blocked',
        libvirt.VIR_DOMAIN_PAUSED:      'paused',
        libvirt.VIR_DOMAIN_SHUTDOWN:    'shutdown',
        libvirt.VIR_DOMAIN_SHUTOFF:     'shutoff',
        libvirt.VIR_DOMAIN_CRASHED:     'crashed',
        libvirt.VIR_DOMAIN_PMSUSPENDED: 'pmsuspended',
    }
    color_state_map = {
        'nostate':     f'{Fore.LIGHTWHITE_EX}nostate{Style.RESET_ALL}',
        'running':     f'{Fore.LIGHTGREEN_EX}running{Style.RESET_ALL}',
        'blocked':     f'{Fore.MAGENTA}blocked{Style.RESET_ALL}',
        'paused':      f'{Fore.LIGHTYELLOW_EX}paused{Style.RESET_ALL}',
        'shutdown':    f'{Fore.RED}shutdown{Style.RESET_ALL}',
        'shutoff':     f'{Fore.RED}shutoff{Style.RESET_ALL}',
        'crashed':     f'{Back.RED}crashed{Style.RESET_ALL}',
        'pmsuspended': f'{Fore.LIGHTYELLOW_EX}pmsuspended{Style.RESET_ALL}',
        'unknown':     f'{Fore.LIGHTYELLOW_EX}unknown{Style.RESET_ALL}',
    }

    with libvirt.open(hypervisor) as conn:
        states = [(dom.name(), state_map.get(dom.state()[0], 'unknown')) for dom in conn.listAllDomains()]

    states.sort(key = lambda x: x[0])
    max_len = 0
    for s in states:
        l = len(s[1])
        if l>max_len: max_len=l        

    libvirt_info = ''
    for dom in states:
        libvirt_info += dom[0][:width-max_len-1].ljust(width-max_len-1)+' '+color_state_map.get(dom[1])+'\n'
    
    return libvirt_info
        

def sysctl_states_map(status):
    # whites = ['alias', 'auto-restart', 'condition', 'disabled', 'elapsed', 'exited', 'final-sigkill', 'final-sigterm', 'final-watchdog', 'inactive', 'indirect', 'linked', 'linked-runtime', 'reload', 'reload-notify', 'reload-signal', 'start', 'start-chown', 'start-post', 'start-pre', 'static', 'stop', 'stop-post', 'stop-pre', 'stop-pre-sigkill', 'stop-pre-sigterm', 'stop-sigkill', 'stop-sigterm', 'stop-watchdog', 'stub', 'tentative', 'transient']
    greens = ['activating-done', 'active', 'enabled', 'enabled-runtime', 'generated', 'listening', 'loaded', 'merged', 'mounted', 'mounting-done', 'plugged', 'running']
    yellows = ['activating', 'auto-restart-queued', 'cleaning', 'deactivating', 'deactivating-sigkill', 'deactivating-sigterm', 'maintenance', 'masked', 'masked-runtime', 'mounting', 'reloading', 'remounting', 'remounting-sigkill', 'remounting-sigterm', 'unmounting', 'unmounting-sigkill', 'unmounting-sigterm', 'waiting']
    reds = ['abandoned', 'bad', 'bad-setting', 'dead', 'dead-before-auto-restart', 'dead-resources-pinned', 'error', 'failed', 'failed-before-auto-restart', 'not-found']
    
    if status in greens:
        return f'{Fore.LIGHTGREEN_EX}{status}{Style.RESET_ALL}'
    elif status in yellows:
        return f'{Fore.LIGHTYELLOW_EX}{status}{Style.RESET_ALL}'
    elif status in reds:
        return f'{Fore.RED}{status}{Style.RESET_ALL}'
    else:
        return status
    

def do_sysctl(width:int, *units:str):
    my_units = subprocess.run(['systemctl', 'list-units', '--failed', '--quiet', '--plain'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode()
    if units:
        my_units += subprocess.run(['systemctl', 'list-units', '--all', '--quiet', '--plain', *units], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode()
    
    my_units = [u.split(' ', 4) for u in re.sub('  *', ' ', my_units).strip().split('\n') if u]
    my_units = [(splitext(u[0])[0], u[3]) for u in my_units]
    max_len = 0
    for u in my_units:
        l = len(u[1])
        if l>max_len: max_len=l
        
    sysctl_info = ''
    seen_units = []
    for u in my_units:
        if u[0] not in seen_units:
            sysctl_info += u[0][:width-max_len-1].ljust(width-max_len-1)+' '+sysctl_states_map(u[1])+'\n'
            seen_units.append(u[0])
        
    return sysctl_info
    

class Systemctl(BaseModule):

    def __init__(self, *, units:list[str]=[], domain:str=None, **kwargs):
        self.units=units
        self.domain=domain
        super().__init__(**kwargs)

    def __call__(self):
        out = ""
        # out += '[red]Services:[/red]' + '\n'
        out += do_sysctl(self.content_size.width, *self.units) + '\n'
        if self.domain:
            out += '[red]VMs:[/red]' + '\n'
            out += do_libvirt(self.content_size.width, self.domain) + '\n'
        out += '[red]Docker containers:[/red]' + '\n'
        try:
            out += do_docker(self.content_size.width, ) + '\n'
        except FileNotFoundError:
            out += '[yellow]Docker not installed[/yellow]'
        return out

widget = Systemctl