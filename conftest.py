"""
pytest configuration for JTTBH test suite.

Adds the project root to sys.path so all app and test imports resolve
correctly without installing the package.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
