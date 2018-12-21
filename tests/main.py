import unittest
import os
import sys

path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)


def get_test_filename():
    file_names = os.listdir(os.getcwd())
    return [name for name in file_names if name.startswith('test_')]


def import_test_module(names):
    return [__import__(name.split('.')[0]) for name in names]


def main():
    names = get_test_filename()
    import_test_module(names)
    unittest.main()

if __name__ == '__main__':
    main()