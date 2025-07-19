from .basemodule import BaseModule, ErrorModule, Coordinates
from .tablemodule import TableModule

GenericModule = BaseModule | ErrorModule | TableModule