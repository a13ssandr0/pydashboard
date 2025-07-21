from .basemodule import BaseModule, Coordinates, ErrorModule
from .tablemodule import TableModule

GenericModule = BaseModule | ErrorModule | TableModule
