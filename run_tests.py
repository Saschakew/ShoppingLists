#!/usr/bin/env python
import unittest
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == '__main__':
    # Discover and run all tests
    test_suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())
