from .basemodule import BaseModule, ErrorModule
from utils.types import Coordinates, Size
from .tablemodule import TableModule

GenericModule = BaseModule | ErrorModule | TableModule
