#!/usr/bin/env python3
"""
Archived E2E script (renamed to avoid pytest discovery).
"""
from pathlib import Path
import sys

_p = Path(__file__).with_suffix('.py')
print('Archived copy of E2E script at', _p)
