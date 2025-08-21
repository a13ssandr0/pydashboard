PyDashboard config file (refer to [Getting stated](getting_started.md/#configyml) for file location)
contains all the settings of the modules and their positions on the screen. The syntax of the file is YAML
([What is YAML?](https://yaml.org)).

Configuration has four main sections, the example below can be used as a starting point for 
building your own configuration file.
```yaml
ansi_color: false
defaults:
  border: ["round", "cyan"]
  title_color: lightgreen
  refresh_interval: 1
grid:
  columns: [10, 10, 10, 10]
  rows: [9, 7, 3, 7, 5]
mods:
  clock:
    position:
      top: 0
      left: 3
      height: 1
      width: 1
```
!!! note
    Keys can be written both in `camelCase` and `snake_case` and are case-insensitive (`bORdeR` is the same as `border`).

## Modules and widgets
PyDashboard provides several modules, each one can be loaded to be displayed in a widget. Usually, when you want to
place a new widget, you just need to add a new entry with the module name under the `mods:` section.

Sometimes you may need to add multiple widgets based on the same module (for example multiple 
[`cmdrunner`](modules/cmdrunner.md) widgets), in these cases you can use another name as key of the entry and then
specify the module type in the configuration of the widget.
```yaml
# ...
mods:
  # ...
  custom_module_one:
    # ...
    type: cmdrunner
  custom_module_two:
    # ...
    type: cmdrunner
```

If you don't like this syntax because it's too much verbose, you can also append a `%` to the module name, followed by
a custom name or identifier (it can even be only a number).

<div class="grid cards" markdown>
```yaml
# ...
mods:
  # ...
  cmdrunner%module_one:
    # ...
  cmdrunner%module_two:
    # ...
```

```yaml
# ...
mods:
  # ...
  cmdrunner%1:
    # ...
  cmdrunner%2:
    # ...
```
</div>


## Positioning
The terminal can be considered like a screen with pixels, but in this case the "pixels" are 
the individual characters, for example a 80x50 terminal means 80 characters wide and 50 characters tall.

!!! note "Getting terminal size"
    To know the size of the terminal that will host PyDashboard run `stty -a`. 
    The first row will output the required information.
    ``` hl_lines="1"
    speed 38400 baud; rows 50; columns 160; line = 0;
    intr = ^C; quit = ^\; erase = ^?; kill = ^U; eof = ^D; eol = <undef>; eol2 = <undef>; swtch = <undef>; start = ^Q; stop = ^S; susp = ^Z; rprnt = ^R; werase = ^W; lnext = ^V; discard = ^O; min = 1; time = 0;
    -parenb -parodd -cmspar cs8 hupcl -cstopb cread -clocal -crtscts
    -ignbrk -brkint -ignpar -parmrk -inpck -istrip -inlcr -igncr -icrnl -ixon -ixoff -iuclc -ixany -imaxbel iutf8
    opost -olcuc -ocrnl onlcr -onocr -onlret -ofill -ofdel nl0 cr0 tab0 bs0 vt0 ff0
    -isig -icanon -iexten -echo echoe echok -echonl -noflsh -xcase -tostop -echoprt echoctl echoke -flusho -extproc
    ```

Using the characters as reference, placing the widgets on the dashboard can be done in two ways:

- grid (recommended)
- windowed

!!! note

    Both methods can be used in the same file, but if both are set for a widget at the same time, 
    the grid takes precedence. 

### Grid
This method splits the screen in chunks of characters.
```yaml
grid:
  columns: [10, 10, 10, 10]
  rows: [5, 7, 3]
```
This example splits the screen in 4 columns of 10 characters each and 3 rows of 5, 7 and 3 characters
respectively, starting from the top left corner of the screen, the remaining space is left unused.
```
----------------------------------------
|        ||        ||        ||        |
|    1   ||    2   ||    3   ||    4   |
|        ||        ||        ||        |
----------------------------------------
----------------------------------------
|        ||        ||        ||        |
|        ||        ||        ||        |
|    5   ||    6   ||    7   ||    8   |
|        ||        ||        ||        |
|        ||        ||        ||        |
----------------------------------------
----------------------------------------
|    9   ||   10   ||   11   ||   12   |
----------------------------------------
```
As you can see the effective size of each widget is smaller than the specified size due to the
border, this behaviour can be controlled by [setting the border](containers/basemodule.md#basemodule.BaseModule--border).

Back to the example above, let's place the clock: inside the `mods:` section we define a `clock:`
section with a `position:` section that requires 4 parameters:
```yaml
# ...
mods:
  # ...
  clock:
    position:   #place the widget in the square number 4
      top: 0    #first row
      left: 3   #fourth column
      height: 1
      width: 1
  # ...
```

If you have a widget that you want to span across multiple rows/columns choose the first square and then
define height and width:

=== "1x1"

    ```
    ----------------------------------------
    |        ||        ||        ||        |
    |  Clock ||    2   ||    3   ||    4   |          position:
    |        ||        ||        ||        |            top: 0
    ----------------------------------------            left: 0
    ----------------------------------------            height: 1
    |        ||        ||        ||        |            width: 1
    |        ||        ||        ||        |
    |    5   ||    6   ||    7   ||    8   |
    |        ||        ||        ||        |
    |        ||        ||        ||        |
    ----------------------------------------
    ----------------------------------------
    |    9   ||   10   ||   11   ||   12   |
    ----------------------------------------
    ```

=== "1x2"

    ```
    ----------------------------------------
    |                  ||        ||        |
    |      Clock       ||    3   ||    4   |          position:
    |                  ||        ||        |            top: 0
    ----------------------------------------            left: 0
    ----------------------------------------            height: 1
    |        ||        ||        ||        |            width: 2
    |        ||        ||        ||        |
    |    5   ||    6   ||    7   ||    8   |
    |        ||        ||        ||        |
    |        ||        ||        ||        |
    ----------------------------------------
    ----------------------------------------
    |    9   ||   10   ||   11   ||   12   |
    ----------------------------------------
    ```

=== "2x1"

    ```
    ----------------------------------------
    |        ||        ||        ||        |
    |        ||    2   ||    3   ||    4   |          position:
    |        ||        ||        ||        |            top: 0
    |        |------------------------------            left: 0
    |  Clock |------------------------------            height: 2
    |        ||        ||        ||        |            width: 1
    |        ||        ||        ||        |
    |        ||    6   ||    7   ||    8   |
    |        ||        ||        ||        |
    |        ||        ||        ||        |
    ----------------------------------------
    ----------------------------------------
    |    9   ||   10   ||   11   ||   12   |
    ----------------------------------------
    ```

=== "2x2"

    ```
    ----------------------------------------
    |                  ||        ||        |
    |                  ||    3   ||    4   |          position:
    |                  ||        ||        |            top: 0
    |                  |--------------------            left: 0
    |                  |--------------------            height: 2
    |      Clock       ||        ||        |            width: 2
    |                  ||        ||        |
    |                  ||    7   ||    8   |
    |                  ||        ||        |
    |                  ||        ||        |
    ----------------------------------------
    ----------------------------------------
    |    9   ||   10   ||   11   ||   12   |
    ----------------------------------------
    ```

### Windowed
If you prefer working directly with widget sizes and absolute coordinates you can use the `window:` 
section instead of `position:`, this enables you to place widgets with more freedom easily, even
overlapping them if you wish.

`window:` requires the following parameters:
```yaml
# ...
mods:
  # ...
  clock:
    window:
      y: 5
      x: 13
      w: 20
      h: 7
  # ...
```
Producing this result:
```
             |
             |
           y |
             |
     x      \ /
-----------> *-------------------
             |                  |  
             |                  |
             |       Clock      | h
             |                  |
             |                  |
             --------------------
                       w
```


## Defaults and common settings
When applying certain settings, for example [styles](containers/basemodule.md#basemodule.BaseModule--styling), you may need apply the same settings to every widget
without having to repeat them many times across the file.

In the `defaults:` section you can define default values for each parameter accepted by a widget, then, when 
initializing it, settings will be evaluated in this order (first takes precedence):

1. widget specific settings
```yaml
# ...
mods:
  # ...
  clock:
    border: ["double", "green"]
  # ...
```

2. `defaults:`
```yaml
defaults:
  border: ["round", "cyan"]
```

3. default values defined in module code. See [BaseModule](containers/basemodule.md)
```python
def __init__(
    ...
    border: ... = ("round", "white"),
    ...
)
```


This example sets the default border to round, cyan, the title color to green and the refresh interval to 1 second
```yaml
defaults:
  border: ["round", "cyan"]
  title_color: lightgreen
  refresh_interval: 1
```


## Color scheme
When running PyDashboard in a TTY without a graphical terminal, some colors may appear wrong due to different
color schemes settings between GUI terminals (for example KDE Konsole) and the kernel text mode (the one
used in systems without a GUI, like Ubuntu Server).

To fix this problem you can set `ansi_color: true` in the configuration.

<div class="grid" markdown>
![ansi_color: false](images/config_ansi_off.jpg)
/// caption
`ansi_color: false`
///

![ansi_color: true](images/config_ansi_on.jpg)
/// caption
`ansi_color: true`
///
</div>

Notice how red in ResourceUsage became magenta and yellow in NUT became orange with `ansi_color: false`.

This fix is not needed if PyDashboard is running in a GUI terminal, as it supports extended ANSI colors and
this setting effectively does nothing, except for using the terminal background rather than painting it all black.

<div class="grid" markdown>
![ansi_color: false](images/config_ansi_off_gui.png)
/// caption
`ansi_color: false`
///

![ansi_color: true](images/config_ansi_on_gui.png)
/// caption
`ansi_color: true`
///
</div>

See: [Textual App Basics - ANSI Colors](https://textual.textualize.io/guide/app/#ansi-colors)