!!! warning "Compatibility"
    PyDashboard has been developed and tested only on Linux based systems and
    is not guaranteed to work on Windows nor macOS due to some modules being
    heavily dependent on Linux specific programs/commands.

If not already present, install pipx following the [official guide](https://pipx.pypa.io/stable/installation/#on-linux).
To install pipx on Ubuntu 23.04 or above run:
```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
# optional to allow pipx actions with --global argument
sudo pipx ensurepath --global
```

Then you can install PyDashboard using the command below:
```bash
pipx install pydashboard
```

### libvirt
If you want to use the [libvirt module](modules/libvirt.md) you have to install
`libvirt-dev` and then install `pydashboard[libvirt]` instead of `pydashboard`.

On Ubuntu you can run:
```bash
sudo apt install libvirt-dev gcc python3-dev
pipx install pydashboard[libvirt]
```


## Running
Once installed you can run PyDashboard using:
```bash
pydashboard <path/to/config.yml>
```

### Command line arguments
#### `config.yml`
Path to the [configuration file](config_file.md).
Defaults to `$HOME/.config/pydashboard/config.yml`.

#### `--log <path>`
Specify log folder, if not specified the log folder will be created 
in `$HOME/.log/pydashboard`, if an exception occurs will be created
in the same folder where the configuration file is stored.

#### `--debug`
Enables debug logging

