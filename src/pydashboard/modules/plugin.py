from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


class Plugin:

    def __new__(cls, *, mpath, mname=None, **kwargs):
        if mname is None:
            mname = Path(mpath).stem
        spec = spec_from_file_location(mname, mpath)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.widget(**kwargs)


widget = Plugin
