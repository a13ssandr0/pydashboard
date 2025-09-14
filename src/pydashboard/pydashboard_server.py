from importlib import import_module

import rpyc
from loguru import logger
from rpyc import ThreadedServer
rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True


# noinspection PyUnboundLocalVariable
if not __package__:
    # Make CLI runnable from source tree with python src/package
    import os, sys

    __package__ = os.path.basename(os.path.dirname(__file__))
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)


class PyDashboardServer(rpyc.Service):
    module = None
    widget = None

    def exposed_import_module(self, module_name, setter_function):
        self.module = import_module('pydashboard.modules.' + module_name)
        self.setter_function = setter_function

    def exposed_init_module(self, **kwargs):
        self.widget = self.module.widget(**kwargs)
        self.widget.set = self.setter_function
        return self.widget.id

    def exposed_post_init_module(self, *args, **kwargs):
        return self.widget.__post_init__(*args, **kwargs)

    def exposed_call_module(self, *args, **kwargs):
        return self.widget.__call__(*args, **kwargs)


def main():
    server = ThreadedServer(PyDashboardServer, port=60001, protocol_config=rpyc.core.protocol.DEFAULT_CONFIG)
    logger.info('Starting PyDashboardServer on port 60001')
    server.start()


if __name__ == '__main__':
    main()
