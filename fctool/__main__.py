"""
python3 -m fctool ... запустит этот модуль
"""
import sys

from fctool import console_ui

if __name__ == '__main__':
    sys.argv[0] = "python -m fctool"
    console_ui.run()
