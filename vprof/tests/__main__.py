"""Test runner for vprof unit and end-to-end tests."""
import argparse
import sys
import unittest


def main():
    """Discovers and runs unit or end-to-end tests."""
    parser = argparse.ArgumentParser(description='Run vprof tests.')
    parser.add_argument(
        'suite', nargs='?', choices=('unit', 'e2e', 'all'), default='unit',
        help='test suite to run (default: unit)')
    args = parser.parse_args()

    patterns = {
        'unit': ('*_test.py',),
        'e2e': ('*_e2e.py',),
        'all': ('*_test.py', '*_e2e.py'),
    }[args.suite]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for pattern in patterns:
        suite.addTests(loader.discover('vprof/tests', pattern=pattern))

    result = unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
