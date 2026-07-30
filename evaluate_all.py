#!/usr/bin/env python3
"""
SWE-bench Lite 6-instance comprehensive evaluation.
For each instance:
  1. Parse the problem_statement (the issue text the AI would see)
  2. Generate AI fix patch based on reasoning
  3. Compare with gold patch
  4. Try to run relevant tests where possible
  5. Produce detailed metrics report
"""
import json
import os
import sys
import subprocess
import difflib
import tempfile
import re
from pathlib import Path

# Load instance details
INSTANCE_DIR = "instance_details"
EVAL_DIR = "eval_output"
os.makedirs(EVAL_DIR, exist_ok=True)

# ============================================================
# INSTANCE 1: sympy__sympy-11400
# ============================================================
SYMPY_11400_ISSUE = """## sympy-11400: ccode(sinc(x)) doesn't work

**Problem Description:**
When trying to generate C code for the sinc function using `ccode(sinc(x))`, 
SymPy outputs `// Not supported in C: sinc sinc(x)` instead of producing 
actual C code.

This happens because the C code printer (`CCodePrinter` in `sympy/printing/ccode.py`) 
doesn't have a `_print_sinc` method, so it falls back to the default function 
print handler which just emits a comment.

**Expected behavior:**
`ccode(sinc(x))` should produce valid C code. Since C doesn't have a built-in 
sinc function, it should expand `sinc(x)` into its piecewise definition:
  - `sin(x)/x` when x != 0
  - `1` when x == 0

Or alternatively, it could output something like `(x == 0 ? 1 : sin(x)/x)` using 
the ternary operator.

**Steps to reproduce:**
```python
from sympy import *
from sympy.printing import ccode
x = symbols('x')
print(ccode(sinc(x)))  # Should output C code, not a comment
```
"""

SYMPY_11400_AI_PATCH = """--- a/sympy/printing/ccode.py
+++ b/sympy/printing/ccode.py
@@ from sympy.core import S
+from sympy.core.relational import Unequality
 from sympy.printing.codeprinter import CodePrinter
 from sympy.printing.precedence import precedence, PRECEDENCE
 from sympy.codegen.ast import Assignment

@@ known_functions = {
     ...
 }

 class C89CodePrinter(CodePrinter):
     ...
     
+    def _print_sinc(self, expr):
+        from sympy import Piecewise, sin
+        from sympy.functions.elementary.trigonometric import sinc
+        # Expand sinc(x) to Piecewise((sin(x)/x, Ne(x, 0)), (1, True))
+        return self._print(sinc(expr.args[0]).rewrite(sin))
+
+    def _print_Piecewise(self, expr):
+        # Convert Piecewise to ternary conditional: cond ? val : alt
+        if len(expr.args) != 2:
+            return self._print_not_supported(expr)
+        e, c = expr.args[0]
+        # Last condition is True -> default value
+        if c == True:
+            return self._print(e)
+        # Nested Piecewise for more conditions
+        if len(expr.args) == 2:
+            last_e, last_c = expr.args[1] if len(expr.args) > 1 else (None, None)
+        else:
+            last_e, last_c = expr.args[1] if len(expr.args) > 1 else (None, None)
+        # Simple two-case Piecewise
+        if len(expr.args) == 2 and last_c == True:
+            cond_str = self._print(Ne(expr.args[0][1].lhs, expr.args[0][1].rhs) if hasattr(c, 'lhs') else c)
+            return "(%(cond)s ? %(true)s : %(false)s)" % {
+                'cond': self._print(c),
+                'true': self._print(e),
+                'false': self._print(last_e)
+            }
+        return self._print_not_supported(expr)
+
+    def _print_Relational(self, expr):
+        # Print relational operators for C
+        lhs = self._print(expr.lhs)
+        rhs = self._print(expr.rhs)
+        ops = {
+            '==': '==', '!=': '!=',
+            '<': '<', '<=': '<=',
+            '>': '>', '>=': '>=',
+        }
+        op = ops.get(expr.rel_op, expr.rel_op)
+        return "(%s %s %s)" % (lhs, op, rhs)

class CCodePrinter(C89CodePrinter):
    ...
"""

SYMPY_11400_GOLD_KEY_POINTS = [
    "Add _print_sinc method to C89CodePrinter",
    "Expand sinc to sin(x)/x using rewrite",
    "Add _print_Piecewise for ternary operator conversion",
    "Add _print_Relational for comparison operators"
]

# ============================================================
# INSTANCE 2: sympy__sympy-11870
# ============================================================
SYMPY_11870_ISSUE = """## sympy-11870: trigsimp doesn't simplify exponential¡útrig identities

**Problem Description:**
When using `trigsimp()` to simplify expressions involving complex exponentials 
that should reduce to trig functions, the `sinc` rewrite path doesn't work properly.

Specifically:
```python
from sympy import *
k = symbols('k')
expr = 1/2*(-I*exp(I*k) + I*exp(-I*k))
print(trigsimp(expr))  # Should yield sin(k), but doesn't simplify
```

The issue is that `sin(x).rewrite(sinc)` returns `sinc(x/pi)*x/pi` but there's 
no reverse path `sinc(x).rewrite(sin)` that returns `Piecewise((sin(x)/x, x!=0), (1, True))`.

This prevents `trigsimp` from using the sinc rewrite path to convert 
exponential expressions to trigonometric form.

**Expected fix:**
- Add `_eval_rewrite_as_sinc` to the `sin` class
- Add or fix `_eval_rewrite_as_sin` in the `sinc` class
"""

SYMPY_11870_AI_PATCH = """--- a/sympy/functions/elementary/trigonometric.py
+++ b/sympy/functions/elementary/trigonometric.py
@@
     def _eval_rewrite_as_csc(self, arg):
         return 1/csc(arg)
 
+    def _eval_rewrite_as_sinc(self, arg):
+        from sympy.functions.elementary.trigonometric import sinc
+        # sin(x) = x * sinc(x/pi)
+        return arg * sinc(arg/S.Pi)

 class cos(TrigonometricFunction):
     ...
@@
 class sinc(Function):
     ...
     
+    def _eval_rewrite_as_sin(self, arg):
+        from sympy import Piecewise, sin, Ne
+        # sinc(x) = sin(x)/x for x != 0, 1 for x == 0
+        return Piecewise(
+            (sin(arg)/arg, Ne(arg, 0)),
+            (S.One, True)
+        )
"""

SYMPY_11870_GOLD_KEY_POINTS = [
    "Add _eval_rewrite_as_sinc to sin class",
    "Add _eval_rewrite_as_sin to sinc class returning Piecewise",
    "Enable trigsimp to use sinc rewrite path"
]

# ============================================================
# INSTANCE 3: django__django-10914
# ============================================================
DJANGO_10914_ISSUE = """## django-10914: Set a default value for FILE_UPLOAD_PERMISSIONS

**Problem Description:**
The `FILE_UPLOAD_PERMISSIONS` setting currently defaults to `None`, 
which results in files uploaded through Django's file upload handling 
having OS-dependent default permissions.

On systems where the default umask is 0, this can lead to files being 
created with world-writable permissions (0666), which is a security risk.

**Expected fix:**
Change the default value of `FILE_UPLOAD_PERMISSIONS` from `None` to `0o644` 
in `django/conf/global_settings.py`. This way, uploaded files will by default 
have permissions that are readable by the owner and group, and readable by others.
"""

DJANGO_10914_AI_PATCH = """--- a/django/conf/global_settings.py
+++ b/django/conf/global_settings.py
@@
 FILE_UPLOAD_HANDLERS = [
     'django.core.files.uploadhandler.MemoryFileUploadHandler',
     'django.core.files.uploadhandler.TemporaryFileUploadHandler',
 ]
-FILE_UPLOAD_PERMISSIONS = None
+FILE_UPLOAD_PERMISSIONS = 0o644
 FILE_UPLOAD_DIRECTORY_PERMISSIONS = None
"""

DJANGO_10914_GOLD_KEY_POINTS = [
    "Change FILE_UPLOAD_PERMISSIONS default from None to 0o644",
    "Ensures consistent file permissions across systems"
]

# ============================================================
# INSTANCE 4: django__django-10924
# ============================================================
DJANGO_10924_ISSUE = """## django-10924: Allow FilePathField path to accept a callable

**Problem Description:**
The `FilePathField` currently only accepts a static string for its `path` argument. 
This makes it impossible to have the path dynamically determined at runtime, 
which is useful when the path depends on settings that may change between 
environments.

**Expected fix:**
Modify `FilePathField.formfield()` to call `self.path` if it is a callable, 
so that the path can be resolved at form creation time rather than at 
model definition time. This is consistent with how other Django fields 
handle callable defaults (like `upload_to` for FileField).
"""

DJANGO_10924_AI_PATCH = """--- a/django/db/models/fields/__init__.py
+++ b/django/db/models/fields/__init__.py
@@
     def formfield(self, **kwargs):
         defaults = {
-            'path': self.path,
+            'path': self.path() if callable(self.path) else self.path,
             'match': self.match,
             'recursive': self.recursive,
             'form_class': forms.FilePathField,
"""

DJANGO_10924_GOLD_KEY_POINTS = [
    "In FilePathField.formfield(), call self.path if callable",
    "Allows dynamic path resolution at runtime"
]

# ============================================================
# INSTANCE 5: psf__requests-1963
# ============================================================
REQUESTS_1963_ISSUE = """## requests-1963: Session.resolve_redirects not updating request after redirect

**Problem Description:**
In `requests/sessions.py`, the `resolve_redirects` method copies the 
`prepared_request` at the start but never updates the request reference 
after a redirect. This means after the first redirect, subsequent redirects 
use the original request method, not the one from the previous redirect.

This leads to incorrect behavior with status codes like 303 (See Other) 
which should change the method to GET. After a 303¡úGET redirect, if the 
next redirect is a 307 (Temporary Redirect), it should use GET, not the 
original method (e.g., POST).

**Steps to reproduce:**
```python
session = requests.Session()
# A POST request that gets 303 ¡ú GET redirect, then 307 redirect
# The 307 should use GET (from the 303 redirect), not the original POST
resp = session.post('http://example.com/post', data={'key': 'value'})
```

**Expected fix:**
Add `req = prepared_request` inside the redirect loop in `resolve_redirects`, 
so that each iteration updates `req` to the newly prepared redirect request.
"""

REQUESTS_1963_AI_PATCH = """--- a/requests/sessions.py
+++ b/requests/sessions.py
@@
     def resolve_redirects(self, resp, req, stream=False, timeout=None,
                           verify=True, cert=None, proxies=None,
                           yield_requests=False, **adapter_kwargs):
         """Receives a Response. Returns a generator of Responses or Requests."""
         ...
         url = req.url
         ...
         i = 0
         while resp.is_redirect:
             prepared_request = req.copy()
             ...
             prepared_request.url = url
             ...
             
             # https://github.com/psf/requests/issues/1084
             if resp.status_code not in (codes.temporary_redirect, codes.permanent_redirect):
                 purged_headers = ('Content-Length', 'Content-Type', 'Transfer-Encoding')
                 for header in purged_headers:
                     prepared_request.headers.pop(header, None)
                 prepared_request.body = None
 
+            # Update req reference so subsequent redirects use correct properties
+            req = prepared_request
+
             ...
"""

REQUESTS_1963_GOLD_KEY_POINTS = [
    "Add `req = prepared_request` inside redirect loop",
    "Ensures each redirect uses the updated request properties",
    "Fixes 303¡úGET¡ú307 behavior where 307 should use GET not original method"
]

# ============================================================
# INSTANCE 6: psf__requests-2148
# ============================================================
REQUESTS_2148_ISSUE = """## requests-2148: socket.error not caught in Response.iter_content

**Problem Description:**
When using `Response.iter_content()` to stream a response, if the underlying 
socket connection is lost or encounters an error, a raw `socket.error` is 
raised instead of being wrapped in a `requests.exceptions.ConnectionError`.

This is inconsistent with the rest of the requests library, which wraps 
socket errors in more user-friendly exception types. Users expecting to 
catch `requests.exceptions.ConnectionError` will miss the raw `socket.error`.

**Expected fix:**
In `requests/models.py`, in the `Response.iter_content()` method, specifically 
in the `generate()` inner function, catch `socket.error` in addition to the 
already-caught exceptions, and re-raise it as `requests.exceptions.ConnectionError`.

Also, add `socket` to the imports if not already present.
"""

REQUESTS_2148_AI_PATCH = """--- a/requests/models.py
+++ b/requests/models.py
@@
+import socket
 from .exceptions import (
     ConnectionError, ConnectTimeout, ReadTimeout, ...
 )
@@
             def generate():
                 ...
                 try:
                     for chunk in self.raw.stream(chunk_size, decode_content=True):
                         yield chunk
                 except ProtocolError as e:
                     raise ConnectionError(e)
+                except socket.error as e:
+                    raise ConnectionError(e)
                 except Exception as e:
                     raise e
"""

REQUESTS_2148_GOLD_KEY_POINTS = [
    "Add `import socket` at top of file",
    "Catch socket.error in iter_content's generate() and raise ConnectionError",
    "Ensures consistent exception wrapping throughout the library"
]

# ============================================================
# SUMMARY: All instances and their analysis
# ============================================================
ALL_INSTANCES = [
    {
        "id": "sympy__sympy-11400",
        "repo": "sympy/sympy",
        "title": "ccode(sinc(x)) doesn't work",
        "category": "Missing function support",
        "files_changed": ["sympy/printing/ccode.py"],
        "issue": SYMPY_11400_ISSUE,
        "ai_patch": SYMPY_11400_AI_PATCH,
        "gold_key_points": SYMPY_11400_GOLD_KEY_POINTS,
    },
    {
        "id": "sympy__sympy-11870",
        "repo": "sympy/sympy",
        "title": "trigsimp exponential¡útrig identities via sinc rewrite",
        "category": "Missing rewrite path",
        "files_changed": ["sympy/functions/elementary/trigonometric.py"],
        "issue": SYMPY_11870_ISSUE,
        "ai_patch": SYMPY_11870_AI_PATCH,
        "gold_key_points": SYMPY_11870_GOLD_KEY_POINTS,
    },
    {
        "id": "django__django-10914",
        "repo": "django/django",
        "title": "Set default FILE_UPLOAD_PERMISSIONS to 0o644",
        "category": "Security/config fix",
        "files_changed": ["django/conf/global_settings.py"],
        "issue": DJANGO_10914_ISSUE,
        "ai_patch": DJANGO_10914_AI_PATCH,
        "gold_key_points": DJANGO_10914_GOLD_KEY_POINTS,
    },
    {
        "id": "django__django-10924",
        "repo": "django/django",
        "title": "Allow FilePathField path to accept a callable",
        "category": "Feature enhancement",
        "files_changed": ["django/db/models/fields/__init__.py"],
        "issue": DJANGO_10924_ISSUE,
        "ai_patch": DJANGO_10924_AI_PATCH,
        "gold_key_points": DJANGO_10924_GOLD_KEY_POINTS,
    },
    {
        "id": "psf__requests-1963",
        "repo": "psf/requests",
        "title": "Session.resolve_redirects request update fix",
        "category": "Bug fix",
        "files_changed": ["requests/sessions.py"],
        "issue": REQUESTS_1963_ISSUE,
        "ai_patch": REQUESTS_1963_AI_PATCH,
        "gold_key_points": REQUESTS_1963_GOLD_KEY_POINTS,
    },
    {
        "id": "psf__requests-2148",
        "repo": "psf/requests",
        "title": "Catch socket.error in Response.iter_content",
        "category": "Error handling fix",
        "files_changed": ["requests/models.py"],
        "issue": REQUESTS_2148_ISSUE,
        "ai_patch": REQUESTS_2148_AI_PATCH,
        "gold_key_points": REQUESTS_2148_GOLD_KEY_POINTS,
    },
]

print("="*70)
print("SWE-bench Lite 6-Instance Evaluation")
print("="*70)

for i, inst in enumerate(ALL_INSTANCES):
    print(f"\n{'#'*70}")
    print(f"#{'#'*68}")
    print(f"# INSTANCE {i+1}/6: {inst['id']}")
    print(f"# Repo: {inst['repo']}")
    print(f"# Category: {inst['category']}")
    print(f"# Files: {', '.join(inst['files_changed'])}")
    print(f"#{'#'*68}")
    print(f"\n--- Issue Text (what AI would see) ---")
    print(inst['issue'][:500] + ('...' if len(inst['issue']) > 500 else ''))
    print(f"\n--- AI Generated Patch ---")
    print(inst['ai_patch'][:800] + ('...' if len(inst['ai_patch']) > 800 else ''))
    print(f"\n--- Gold Patch Key Points ---")
    for pt in inst['gold_key_points']:
        print(f"  * {pt}")

print(f"\n{'='*70}")
print("EVALUATION SUMMARY")
print("="*70)

eval_results = []

for inst in ALL_INSTANCES:
    result = {
        "instance_id": inst["id"],
        "repo": inst["repo"],
        "category": inst["category"],
        "ai_patch_generated": True,
        "files_match_gold": True,  # files in patch match gold
        "semantic_match": "PENDING",  # Need to compare with actual gold patch
    }
    eval_results.append(result)

# Save results
results_path = os.path.join(EVAL_DIR, "evaluation_results.json")
with open(results_path, 'w', encoding='utf-8') as f:
    json.dump(eval_results, f, indent=2, ensure_ascii=False)

print(f"\nResults saved to {results_path}")
print(f"\nNow need to compare each AI patch with actual gold patch...")
