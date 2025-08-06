from .basemodule import BaseModule, ErrorModule
from .tablemodule import TableModule

GenericModule = BaseModule | ErrorModule | TableModule
