from typing import Tuple, NamedTuple

Coordinates = NamedTuple('Coordinates', [('h', int), ('w', int), ('y', int), ('x', int)])


height = int
width = int
Size = Tuple[height, width]
