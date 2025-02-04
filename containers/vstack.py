from importlib import import_module
from typing import Any

from textual.containers import VerticalGroup

from containers.basemodule import BaseModule, ErrorModule


class Vstack(BaseModule):
    #after module initialization the object is automatically initialized, but
    #linter is not able to detect the change from type to object, so we force it
    inner:VerticalGroup=VerticalGroup
    ready_hooks = {}
    
    def __init__(self, *, mods:dict[str,dict[str,Any]], 
                 defaults:dict[str, Any]={}, 
                 order:list[str]|None=None, **kwargs):
        super().__init__(**kwargs)
        
        self.modules = []
        
        for w_id, conf in mods.items():
            if conf is None: conf = {}
            
            if not conf.get('enabled', True): continue
            
            for k, v in defaults.items():
                conf.setdefault(k ,v)
            
            mod = conf.get('type', w_id.split('%')[0])
            w_id = self.id + '-' + w_id
            
            try:
                m = import_module('modules.'+mod)
                # imported_modules.add(m)
                widget:BaseModule = m.widget(id=w_id, defaults=defaults|conf.pop('defaults',{}), **conf)
            except ModuleNotFoundError as e:
                widget = ErrorModule(f"Module '{mod}' not found\n{e.msg}")
            except AttributeError as e:
                widget = ErrorModule(f"Attribute '{e.name}' not found in module {mod}")
            
            widget.styles.width = "100%"
            widget.styles.height = "auto"
            widget.styles.overflow_x = "hidden"
            # widget.styles.overflow_y = "hidden"
            self.modules.append(widget)

            try:
                self.ready_hooks[w_id] = widget.on_ready
            except AttributeError:
                pass
    
    def __post_init__(self): pass
    def __call__(self): pass
    def update(self): pass
    def _update(self): pass
    def on_ready(self, _): pass
    
    def compose(self):
        self.inner = VerticalGroup(*self.modules)
        self.inner.styles.width = "100%"
        self.inner.styles.height = "100%"
        yield self.inner