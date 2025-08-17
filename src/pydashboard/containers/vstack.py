from collections import OrderedDict
from importlib import import_module
from typing import Any

from textual.containers import VerticalGroup

from pydashboard.containers.basemodule import BaseModule, ErrorModule


class Vstack(BaseModule):
    # after module initialization the object is automatically initialized, but
    # linter is not able to detect the change from type to object, so we force it
    inner: VerticalGroup = VerticalGroup
    ready_hooks = {}

    def __init__(self, *, mods: dict[str, dict[str, Any]], defaults=None, order=None, **kwargs):
        """

        Args:
            mods:
            defaults:
            order:
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(mods=mods, defaults=defaults, order=order, **kwargs)
        if defaults is None:
            defaults = {}
        self.order = [] if order is None else order
        self.modules = OrderedDict()

        defaults['refreshInterval'] = self.refresh_interval

        for w_id, conf in mods.items():
            if conf is None: conf = {}

            if not conf.get('enabled', True): continue

            for k, v in defaults.items():
                conf.setdefault(k, v)

            mod = conf.get('type', w_id.split('%')[0])
            full_w_id = self.id + '-' + w_id

            try:
                m = import_module('pydashboard.modules.' + mod)
                widget: BaseModule | ErrorModule = m.widget(id=full_w_id, defaults=defaults | conf.pop('defaults', {}),
                                                            mod_type=mod, **conf)
            except ModuleNotFoundError as e:
                widget = ErrorModule(f"Module '{mod}' not found\n{e.msg}")
            except ImportError as e:
                widget = ErrorModule(str(e))
            except AttributeError as e:
                widget = ErrorModule(f"Attribute '{e.name}' not found in module {mod}")

            widget.styles.width = "100%"
            widget.styles.height = "auto"
            widget.styles.overflow_x = "hidden"
            # widget.styles.overflow_y = "hidden"
            self.modules[w_id] = widget

            try:
                self.ready_hooks[full_w_id] = widget.on_ready
            except AttributeError:
                pass

    def __post_init__(self):
        pass

    def __call__(self):
        pass

    def update(self):
        pass

    def on_ready(self, _):
        pass

    def compose(self):
        self.inner = VerticalGroup(*[self.modules.pop(mod) for mod in self.order if mod in self.modules],
                                   *self.modules.values())
        self.inner.styles.width = "100%"
        self.inner.styles.height = "100%"
        yield self.inner
