from itertools import chain, repeat


def interleave(l: list, j):
    return list(chain.from_iterable(zip(l, repeat(j))))[:-1]
