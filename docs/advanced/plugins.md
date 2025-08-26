from pydashboard.containers import TableModuleStarting with version 1.1.0, PyDashboard supports plugins, following this guide you can easily make your own script
to extend PyDashboard functionalities.

!!! tip
    Since plugins are built exactly as integrated modules, you can follow the guide also if you want to contribute
    to PyDashboard with a pull request to publish your custom modules. Just remember to make appropriate documentation
    for them.

To start building a plugin you need to set up the development environment:

```bash
sudo apt install python3-virtualenv
virtualenv .venv
source .venv/bin/activate
pip install pydashboard
```

## Printing to the screen

The most basic plugin should be able to print something inside its box each time it gets updated. To do this you have to
implement the `__call__` method.

Each module should subclass one of the available containers, either [BaseModule](../containers/basemodule.md)
or [TableModule](../containers/tablemodule.md). For this simple example we choose to subclass BaseModule.

```python title="helloworld.py"
from pydashboard.containers.basemodule import BaseModule


class HelloWorld(BaseModule):
    def __call__(self):
        return "Hello, World!"
```

This method can return either a string with optional [markup](https://textual.textualize.io/guide/content/) or a
[Rich Text](https://rich.readthedocs.io/en/latest/text.html) object.

To implement PyDashboard modular architecture each module should end defining a variable named `widget` that holds
the reference to the class just implemented.

```python title="helloworld.py" hl_lines="9 10"
from pydashboard.containers.basemodule import BaseModule


class HelloWorld(BaseModule):
    def __call__(self):
        return "Hello, World!"


# DO NOT instantiate the class here
widget = HelloWorld
```

!!! tip
    Using a variable to hold the class reference means that the class itself could be named `widget` and everything would
    work the same. It's true, but calling each module `widget` would be ugly to read in the source code and a nightmare
    to quickly find useful information in the logs.

    Luckily you have **_free will_** and can decide yourself what you prefer.

Save this file as `helloworld.py` everywhere you want and add these lines to your configuration file inside the `mods:`
section.

```yaml title="config.yml"
mods:
  # ...
  helloworld:
    type: plugin
    mpath: /absolute/path/to/helloworld.py
    refresh_interval: 5s
    position: #change as needed
      top: 0
      left: 0
      height: 1
      width: 1
```

Start PyDashboard as usual and your new module should appear on the screen where you placed it.

### Updating content

Feels a bit static, doesn't it? Let's extend the example to change the content at each update.

```python title="beers.py"
from pydashboard.containers.basemodule import BaseModule

from random import randint


class Beers(BaseModule):

    def __call__(self):
        return f"Hello, Bartender! Give me {randint(2, 10)} beers."


widget = Beers
```

## Styling

When updating the widget, you can also update its title, subtitle and style.
For example let's make a simple module that gets three random numbers and sets two of them as the title and subtitle,
and the third as the widget content, we also set the subtitle text color to red.

```python title="randomizer.py"
from pydashboard.containers.basemodule import BaseModule

from random import randint


class Randomizer(BaseModule):

    def __call__(self):
        self.border_title = str(randint(100, 1000))
        self.border_subtitle = str(-randint(100, 1000))
        self.set('styles.border_subtitle_color', 'red')
        return str(randint(1, 100))


widget = Randomizer

```

These are all the attributes of the module you can set using:

```python
self.set(attribute, value)
```

| Attribute                             | Type                                            | Description                                                                            |
|---------------------------------------|-------------------------------------------------|----------------------------------------------------------------------------------------|
| `'styles.align_horizontal'`           | `Literal['left', 'center', 'right', 'justify']` | Horizontal alignment of the text                                                       |
| `'styles.align_vertical'`             | `Literal['top', 'middle', 'bottom']`            | Vertical alignment of the text                                                         |
| `'styles.color'`                      | `str`                                           | [Color](../containers/basemodule.md#basemodule.BaseModule--color) of the text          |
| `'styles.border'`                     | `tuple[str]`                                    | [Border](../containers/basemodule.md#basemodule.BaseModule--border) of the widget      |
| `'border_title'`                      | `str`                                           | Title of the widget                                                                    |
| `'styles.border_title_align'`         | `Literal['left', 'center', 'right', 'justify']` | Alignment of the title                                                                 |
| `'styles.border_title_background'`    | `str`                                           | Background color of the title                                                          |
| `'styles.border_title_color'`         | `str`                                           | [Color](../containers/basemodule.md#basemodule.BaseModule--color) of the title         |
| `'styles.border_title_style'`         | `str`                                           | [Style](../containers/basemodule.md#basemodule.BaseModule--text-style) of the title    |
| `'border_subtitle'`                   | `str`                                           | Subtitle of the widget                                                                 |
| `'styles.border_subtitle_align'`      | `Literal['left', 'center', 'right', 'justify']` | Alignment of the subtitle                                                              |
| `'styles.border_subtitle_background'` | `str`                                           | Background color of the subtitle                                                       |
| `'styles.border_subtitle_color'`      | `str`                                           | [Color](../containers/basemodule.md#basemodule.BaseModule--color) of the subtitle      |
| `'styles.border_subtitle_style'`      | `str`                                           | [Style](../containers/basemodule.md#basemodule.BaseModule--text-style) of the subtitle |

If you let the user choose colors/styles and then you want to temporarily change them, you can make use of the
`#!python self.reset_settings(attribute)` function to restore the default/user values:

```python
self.reset_settings('styles.border_subtitle_color')
```

The example above resets the subtitle color to the default/user settings.

!!! note
    You can explore other configurations for the widget by reading
    the [Textual Styles Reference](https://textual.textualize.io/styles/)
    but be careful because setting attributes directly without `self.set` won't work over SSH.

## Module initialization

Sometimes you may need to run some code only when initializing the module, for example to authenticate for a service,
or to make calculations based on widget sizes, that you can get only after initialization.

PyDashboard provides you the `__init__` and `__post_init__` methods. When choosing which one to use,
please read the following table to choose which one best suits your needs, for long-running code it's better to use the
latter.

| `__init__`                                                                                                                               | `__post_init__`                                                                                                                    |
|------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| Runs in main thread, before full widget graphical initialization.<br> Long initialization tasks will delay all interface initialization. | Runs in a separate thread, after module graphical initialization (i.e.: widget is aware of its size at this moment).               |
| Only handles import exceptions, an unhandled exception crashes the entire program.                                                       | Handles every exception, an unhandled exception will produce a notification and a log record, without crashing the entire program. |
| Runs locally and over SSH.                                                                                                               | Runs on the remote computer if working over SSH.                                                                                   |
| Can define new configuration parameters.                                                                                                 | No need to mess with module configuration parameters.                                                                              |

### `__init__`
Use this method if you want to add configuration parameters to the module or to transform the parameters passed to the
super class.
```python title="greeter.py"
from pydashboard.containers.basemodule import BaseModule


class Greeter(BaseModule):
    def __init__(self, *, name: str, **kwargs):
        # DO NOT FORGET to call the init method of the super class.
        # Pass to it EVERY parameter, 
        # even the ones you are adding, 
        # to allow them to be passed to the server 
        # in the event of a remote connection.
        super().__init__(name=name, **kwargs)
        self._name = name
    
    def __call__(self):
        return f"Hello, {self._name}!"

widget = Greeter
```

!!! warning
    When calling `#!python super().__init__`, always remember to call it as soon as possible inside the `__init__` method.

    Also pass to it **every** new parameter you are defining, this is important to make the module work when using the
    remote connection feature.

### `__post_init__`
Use this method to perform long-running initialization tasks, such as authentication, and graphic interface calculations.

Here are two examples from [QBitTorrent](../modules/qbittorrent.md) and [NUT](../modules/nut.md) modules.

```python title="Source code in src/pydashboard/modules/qbittorrent.py"
--8<-- "src/pydashboard/modules/qbittorrent.py:246:255"
```

```python title="Source code in src/pydashboard/modules/nut.py"
--8<-- "src/pydashboard/modules/nut.py:43:44"
```

## Content size
In the last example above you can notice how the `__post_init__` method has a second argument of type `Size`, this argument
is a tuple `(height, width)` that represents the available content size without the borders.

To get the content size you just need to add an argument in `__call__` and/or `__post_init__` of type `Size` calling it
whatever you want, it will be BaseModule's duty to automatically pass the required argument.

```python title="mysize.py"
from pydashboard.containers import BaseModule
from pydashboard.utils.types import Size


class MySize(BaseModule):
    def __call__(self, size: Size):
        return f"This box is {size[0]} characters tall and {size[1]} characters wide"

widget = MySize
```

## Missing dependencies
If your plugin requires dependencies not installed when installing PyDashboard, you can inject them using:
```bash
pipx inject pydashboard [dependencies ...]
```

## Table based plugins
When creating a plugin you can also make use of the `TableModule` base class instead of `BaseModule`.

Everything explained above is still valid, but this time the `__call__` method requires you to return a pandas Dataframe.

`TableModule` also allows you to set various class attributes to customize how the table is shown.
Set one or more of the following class attributes.
```python
from pydashboard.containers.tablemodule import TableModule 


class MyTable(TableModule):
    column_names = ...
    humanize = ...
    justify = ...
    colorize = ...
```

### `column_names`
Type: `dict[str, str]`

Maps column names from the DataFrame to more human friendly names, if a key is missing will be used the column name
from the dataframe.

### `humanize`
Type: `dict[str, Callable]`

Maps column names from the DataFrame to functions used to transform the content of a column in a human friendly string, 
if a key is missing no transformation is applied.

### `justify`
Type: `dict[str, Literal["default", "left", "center", "right", "full"] | None]`

For each column name specifies the justification direction, if a key is missing the default is `left`.

### `colorize`
Type: `dict[str, Callable]`

Maps column names from the DataFrame to functions used to colorize the content of a column, if a key is missing
no transformation is applied.


## Remote connection
PyDashboard supports running modules on a remote machine and getting the result on the machine running the dashboard,
however **plugin modules over remote connections are not officially supported** yet, to make them work you have to use a
little hack.

The plugin module is only a temporary module that gets replaced as soon as the custom module is loaded, so is not able
to transfer the script on the remote machine, because any reference to the plugin path is loss when it is initialized.

To make the plugin work over remote connection:

1. on both the main machine running PyDashboard and the remote one running PyDashboard Server place the plugin inside
    ```
    /home/USER/.local/share/pipx/venvs/pydashboard/lib/python3.13/site-packages/pydashboard/modules/
    ```
    Remember to change `USER` with your username, also `site-packages` might be inside another folder depending on the 
    Python version installed inside the virtual environment.
2. Load the plugin in the config file like any other integrated module.

!!! warning
    This hack modifies a folder that normally shouldn't be modified, adding files to it means they might be removed/altered
    when updating PyDashboard. Make sure to **always** have a copy of the files added and be prepared to restore them
    (following the procedure above) when you update PyDashboard.