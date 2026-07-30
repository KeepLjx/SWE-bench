# Fix Python 3.12 compatibility for sympy 1.0
import collections
import collections.abc
import re
collections.Mapping = collections.abc.Mapping
collections.MutableMapping = collections.abc.MutableMapping
collections.Callable = collections.abc.Callable
collections.Iterable = collections.abc.Iterable
collections.Hashable = collections.abc.Hashable

# Also patch the 're' module issue
import importlib
import builtins

# Now test ccode with sinc
import sys
sys.path.insert(0, r"D:\workspace\QTCTest\projects\Trae CN\SWE-bench\repos\sympy")
from sympy import ccode, sinc, symbols
x = symbols('x')
print("ccode(sinc(x)) =", ccode(sinc(x)))
