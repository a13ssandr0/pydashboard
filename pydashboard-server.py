from importlib import import_module

import rpyc
from rpyc import ThreadedServer
from loguru import logger


class PyDashboardServer(rpyc.Service):
    module = None
    widget = None

    def exposed_import_module(self, module_name, setter_function):
        self.module = import_module('modules.' + module_name)
        self.setter_function = setter_function

    def exposed_init_module(self, **kwargs):
        self.widget = self.module.widget(**kwargs)
        self.widget.set = self.setter_function
        return self.widget.id

    def exposed_post_init_module(self, *args, **kwargs):
        return self.widget.__post_init__(*args, **kwargs)

    def exposed_call_module(self, *args, **kwargs):
        return self.widget.__call__(*args, **kwargs)


if __name__ == '__main__':
    server = ThreadedServer(PyDashboardServer, port=60001)
    logger.info('Starting PyDashboardServer on port 60001')
    server.start()