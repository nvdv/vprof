"""Main test module."""
import unittest
import profile_test


if __name__ == '__main__':
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner()
    runner.run(loader.loadTestsFromModule(profile_test))
