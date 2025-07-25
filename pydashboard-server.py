from importlib import import_module

import rpyc
from rpyc import ThreadedServer
from loguru import logger


class PyDashboardServer(rpyc.Service):
    modules = {}

    def exposed_init_module(self, module_name, _id, **kwargs):
        widget = import_module('modules.' + module_name).widget(id=_id, **kwargs)
        self.modules[_id] = widget
        return widget.id

    def exposed_post_init_module(self, _id, *args, **kwargs):
        return self.modules[_id].__post_init__(*args, **kwargs)

    def exposed_call_module(self, _id, *args, **kwargs):
        return self.modules[_id].__call__(*args, **kwargs)


if __name__ == '__main__':
    server = ThreadedServer(PyDashboardServer, port=60001)
    logger.info('Starting PyDashboardServer on port 60001')
    server.start()