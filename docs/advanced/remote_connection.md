A key feature of PyDashboard is the ability to connect remotely to another computer running PyDashboard to run the
module backend on the remote computer and display the widget on the local computer. You can even have multiple widget
getting content from the same remote computer and/or multiple remote computers.

Each module supports the following parameters to set up an SSH connection to a computer running PyDashboard server:

| Parameter                    | Description                                                   |
|------------------------------|---------------------------------------------------------------|
| remote_host                  | Remote host IP or FQDN                                        |
| remote_port                  | Remote host SSH port                                          |
| remote_username              | Remote host SSH username                                      |
| remote_password              | Remote host SSH password (see note below)                     |
| remote_key                   | Remote host SSH key                                           |
| ssh_strict_host_key_checking | Control host key verification behaviour                       |
| ssh_ignore_known_hosts_file  | Ignore known hosts file (suppresses host key changed warning) |

!!! danger "Danger: security risk"
    Saving passwords (`remote_password`) in the configuration file is strongly discouraged and should be avoided unless key based
    authentication is not possible, in such cases `sshpass` needs to be installed, and it's recommended to save the 
    configuration file not world-readable:
    ```bash
    chmod 700 .config/pydashboard/config.yml
    ```

For the purpose of this guide we will be calling `server` the remote computer running PyDashboard server, that will
be providing data to the computer running PyDashboard and displaying the widgets on its screen,
that will be called `client`.


## Autostart on servers
### 1. Users preparation
To set up remote connection it's suggested to have an unprivileged user on the server that can be used to connect 
to the server itself.

The following commands will present a title to tell if they have to be run on the server(s) or on the client. 

```bash title="client"
#replace USER with your current user on the server
scp $(ls -dt "${HOME}"/.ssh/id*.pub 2>/dev/null | grep -v -- '-cert.pub$' | head -n 1) USER@server:client_id.pub
```

!!! note
    If the command above returns
    ```
    usage: scp [-346ABCOpqRrsTv] [-c cipher] [-D sftp_server_path] [-F ssh_config]
               [-i identity_file] [-J destination] [-l limit] [-o ssh_option]
               [-P port] [-S program] [-X sftp_option] source ... target
    ```
    this means that your user has not a key file and you have to create one. 
    To do it just run `ssh-keygen` accepting the default settings.

```bash title="server"
# create a user specifically for pydashboard 
sudo useradd --create-home --shell /bin/bash pydashboard
#create .ssh directory to save authorized_keys file
sudo mkdir -p /home/pydashboard/.ssh
# copy the ssh key from the current user to pydashboard user authorized keys 
cat client_id.pub | sudo tee -a /home/pydashboard/.ssh/authorized_keys > /dev/null
# remove the temporary file
rm client_id.pub
```

!!! note
    If you plan to use `docker` and/or `libvirt` modules make sure to set appropriate permissions to the pydashboard user on
    the server:
    ```bash
    sudo addgroup docker
    sudo adduser pydashboard docker
    
    sudo addgroup libvirt
    sudo adduser pydashboard libvirt
    ```

### 2. Installation
For installation refer to [Getting started](../getting_started.md). 

!!! note
    ~~If at least one of the servers will be using the module libvirt, remember to 
    [install `pydashboard[libvirt]`](../getting_started.md/#libvirt)
    on both che client and the server needing that module, other servers are not affected.~~
    Starting from version 1.2.0 you don't need anymore to install libvirt library on the client if you only plan to
    run the module on the servers.


### 3. Systemd unit


On each server create a new systemd unit file

```bash
sudo nano /etc/systemd/system/pydashboard-server.service
```

and paste this content
``` title="/etc/systemd/system/pydashboard-server.service"
[Unit]
Description=PyDashboard server
After=multi-user.target 

[Service]
Environment="PYTHONUNBUFFERED=1"
User=pydashboard
ExecStart=/home/pydashboard/.local/bin/pydashboard-server
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service
```bash
sudo systemctl enable pydashboard-server.service
sudo systemctl start pydashboard-server.service
```

## Client connection
On the client, in the configuration file, for each widget you want to get data from the server, add the parameter
`#!yaml remote_host: pydashboard@<ip_addr>`.

```yaml title="Full example"
mods:
  resourceusage%pc2:
    remote_host: 192.168.1.4
    subtitle: PC2
    position:
      top: 5
      left: 0
      height: 3
      width: 1
    cpuCombined: true
    showCPU: true
    showMem: true
    showSwp: false
    showGPU: true
    refreshInterval: 5
```

If you set up everything correctly and the service on the server has started,
you should see the data coming from the server in the widget.


## SSH key verification

When connecting via SSH, the remote device (host) sends to the one that wants to connect its public key,
the computer starting the conection verifies if it has already seen that host with that key.
If the host was never seen before, `ssh` asks if you want to accept the new key and connect. If the host was
already seen but its key changed, a warning is printed on the screen and the connection immediately aborted.

Although not recommended, PyDashboard can handle these cases for you by setting

- ssh_strict_host_key_checking: <br> 
  Can be set to `null`, `true`, `false` or `accept-new`. <br>
  If set to `false` or `accept-new` new hosts will be added to known hosts without complaining.
  See [StrictHostKeyChecking](#stricthostkeychecking)

- ssh_ignore_known_hosts_file: <br>
  Even after setting `#!yaml ssh_strict_host_key_checking: accept-new` or `#!yaml ssh_strict_host_key_checking: false`,
  `ssh` may still display a warning if the host key changed and prohibit you from connecting, if this parameter
  is set to `true` UserKnownHostsFile will be set to `/dev/null`, meaning no file has to be checked for known hosts.

!!! danger
    The settings above could be a security risk if misused and should be avoided where possible.

### StrictHostKeyChecking
Source: [man ssh_config(5)](https://man7.org/linux/man-pages/man5/ssh_config.5.html)

> If this flag is set to **yes**, ssh(1) will never
> automatically add host keys to the ~/.ssh/known_hosts
> file, and refuses to connect to hosts whose host key has
> changed. This provides maximum protection against man-in-
> the-middle (MITM) attacks, though it can be annoying when
> the /etc/ssh/ssh_known_hosts file is poorly maintained or
> when connections to new hosts are frequently made. This
> option forces the user to manually add all new hosts.
>
> If this flag is set to **accept-new** then ssh will
> automatically add new host keys to the user's known_hosts
> file, but will not permit connections to hosts with
> changed host keys.
>
> If this flag is set to **no** or **off**, ssh
> will automatically add new host keys to the user known
> hosts files and allow connections to hosts with changed
> hostkeys to proceed, subject to some restrictions.
>
> If this flag is set to **ask** (the default), new host keys will
> be added to the user known host files only after the user
> has confirmed that is what they really want to do, and ssh
> will refuse to connect to hosts whose host key has
> changed. The host keys of known hosts will be verified
> automatically in all cases.

| ssh          | Python         | yaml (configuration file) |
|--------------|----------------|---------------------------|
| `yes`        | `True`         | `yes`/`true`/`on`         |
| `accept-new` | `'accept-new'` | `accept-new`              |
| `no`/`off`   | `False`        | `no`/`false`/`off`        |
| `ask`        | `None`         | `null` (or not set)       |


### UserKnownHostsFile
Source: [man ssh_config(5)](https://man7.org/linux/man-pages/man5/ssh_config.5.html)

> Specifies one or more files to use for the user host key
> database, separated by whitespace.  Each filename may use
> tilde notation to refer to the user's home directory, the
> tokens described in the “TOKENS” section and environment
> variables as described in the “ENVIRONMENT VARIABLES”
> section.  A value of none causes ssh(1) to ignore any
> user-specific known hosts files.  The default is
> ~/.ssh/known_hosts, ~/.ssh/known_hosts2.





## Uninstalling from server

```
sudo systemctl stop pydashboard-server.service
sudo systemctl disable pydashboard-server.service
sudo rm /etc/systemd/system/pydashboard-server.service
sudo deluser pydashboard --remove-home
```

