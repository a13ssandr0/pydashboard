#!/usr/bin/env python
"""
A simple cmd-line tool for displaying FormattingString capabilities.

For example:

$ python tprint.py bold A rather bold statement.
"""
# std
from __future__ import print_function

# std imports
import argparse

# local
from blessed import Terminal


def parse_args():
    """Parse sys.argv, returning dict suitable for main()."""
    parser = argparse.ArgumentParser(
        description='displays argument as specified style')

    parser.add_argument('style', type=str, help='style formatter')
    parser.add_argument('text', type=str, nargs='+')

    return dict(parser.parse_args(['bold'])._get_kwargs())


def main(style, text):
    """Program entry point."""
    term = Terminal()
    style = getattr(term, style)
    print("\033[0;32mON \033[0m")


if __name__ == '__main__':
    main('bold', 'a rather bold statement')
    input()