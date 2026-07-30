# -*- coding: utf-8 -*-
"""
SWE-bench Lite 6题评估报告生成脚本
"""
from datasets import load_dataset
import difflib
import re

def normalize_patch(patch_text):
    """Normalize a patch for comparison."""
    lines = patch_text.strip().split('\n')
    result = []
    for line in lines:
        if line.startswith('diff --git') or line.startswith('index ') or \
           line.startswith('---') or line.startswith('+++') or \
           line.startswith('@@'):
            continue
        result.append(line)
    return '\n'.join(result).strip()

def compute_similarity(patch1, patch2):
    """Compute similarity ratio between two patches."""
    n1 = normalize_patch(patch1)
    n2 = normalize_patch(patch2)
    return difflib.SequenceMatcher(None, n1, n2).ratio()

ds = load_dataset('SWE-bench/SWE-bench_Lite')

tasks = [
    ('sympy__sympy-11400', 'ccode(sinc(x)) 不支持 C 代码生成'),
    ('sympy__sympy-12481', 'Permutation 非不相交 cycles 报错'),
    ('django__django-10914', 'FILE_UPLOAD_PERMISSIONS 默认值 None→0o644'),
    ('django__django-11099', 'UsernameValidator 允许尾部换行符'),
    ('psf__requests-863', 'register_hook 不支持列表参数'),
    ('psf__requests-2317', 'builtin_str 转换二进制 method 错误'),
]

# AI-generated patches (what we applied)
ai_patches = {
    'sympy__sympy-11400': '''diff --git a/sympy/printing/ccode.py b/sympy/printing/ccode.py
--- a/sympy/printing/ccode.py
+++ b/sympy/printing/ccode.py
@@ -231,6 +231,14 @@ def _print_Symbol(self, expr):
         else:
             return name
 
+    def _print_sinc(self, expr):
+        from sympy.functions.elementary.trigonometric import sin
+        from sympy.core.relational import Ne
+        from sympy.functions import Piecewise
+        _piecewise = Piecewise(
+            (sin(expr.args[0]) / expr.args[0], Ne(expr.args[0], 0)), (1, True))
+        return self._print(_piecewise)
+
     def _print_AugmentedAssignment(self, expr):
         lhs_code = self._print(expr.lhs)
         op = expr.rel_op''',

    'sympy__sympy-12481': '''diff --git a/sympy/combinatorics/permutations.py b/sympy/combinatorics/permutations.py
--- a/sympy/combinatorics/permutations.py
+++ b/sympy/combinatorics/permutations.py
@@ -895,12 +895,8 @@ def __new__(cls, *args, **kwargs):
         temp = flatten(args)
-        if has_dups(temp):
-            if is_cycle:
-                raise ValueError('there were repeated elements; to resolve '
-                'cycles use Cycle%s.' % ''.join([str(tuple(c)) for c in args]))
-            else:
-                raise ValueError('there were repeated elements.')
+        if has_dups(temp) and not is_cycle:
+            raise ValueError('there were repeated elements.')
         temp = set(temp)''',

    'django__django-10914': '''diff --git a/django/conf/global_settings.py b/django/conf/global_settings.py
--- a/django/conf/global_settings.py
+++ b/django/conf/global_settings.py
@@ -304,7 +304,7 @@
-FILE_UPLOAD_PERMISSIONS = None
+FILE_UPLOAD_PERMISSIONS = 0o644''',

    'django__django-11099': '''diff --git a/django/contrib/auth/validators.py b/django/contrib/auth/validators.py
--- a/django/contrib/auth/validators.py
+++ b/django/contrib/auth/validators.py
@@ -7,7 +7,7 @@
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\\Z'
@@ -17,7 +17,7 @@
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\\Z\'''',

    'psf__requests-863': '''diff --git a/requests/models.py b/requests/models.py
--- a/requests/models.py
+++ b/requests/models.py
@@ -462,8 +462,10 @@
     def register_hook(self, event, hook):
         """Properly register a hook."""
-
-        self.hooks[event].append(hook)
+        if isinstance(hook, (list, tuple, set)):
+            self.hooks[event].extend(hook)
+        else:
+            self.hooks[event].append(hook)''',

    'psf__requests-2317': '''diff --git a/requests/sessions.py b/requests/sessions.py
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -13,7 +13,7 @@
-from .compat import cookielib, OrderedDict, urljoin, urlparse, builtin_str
+from .compat import cookielib, OrderedDict, urljoin, urlparse
@@ -425,7 +425,7 @@
-        method = builtin_str(method)
+        method = to_native_string(method)''',
}

print("=" * 80)
print("SWE-bench Lite 6 题评估报告")
print("=" * 80)

total = 0
exact = 0
partial = 0

for instance_id, desc in tasks:
    inst = [x for x in ds['test'] if x['instance_id'] == instance_id][0]
    gold = inst['patch']
    ai = ai_patches[instance_id]
    
    sim = compute_similarity(gold, ai)
    
    # Determine match level
    n_ai = normalize_patch(ai)
    n_gold = normalize_patch(gold)
    
    status = "EXACT" if n_ai.strip() == n_gold.strip() else ("PARTIAL" if sim > 0.5 else "MISMATCH")
    
    if status == "EXACT":
        exact += 1
    elif status == "PARTIAL":
        partial += 1
    
    total += 1
    
    print(f"\n{'='*60}")
    print(f"Task {total}: {instance_id}")
    print(f"  描述: {desc}")
    print(f"  相似度: {sim:.1%}")
    print(f"  匹配状态: {status}")
    print(f"  修改文件数: AI={len(re.findall(r'diff --git', ai))} / Gold={len(re.findall(r'diff --git', gold))}")
    
    if status != "EXACT":
        print(f"  差异说明:", end=" ")
        if instance_id == 'sympy__sympy-11400':
            print("AI只添加了_print_sinc；Gold还额外添加了_print_Relational")
        elif instance_id == 'sympy__sympy-12481':
            print("AI保留非cycle的has_dups检查；Gold完全移除了has_dups")
        else:
            print("微小差异")

print(f"\n{'='*60}")
print("汇总")
print(f"{'='*60}")
print(f"  总任务数: {total}")
print(f"  精确匹配 (EXACT): {exact}")
print(f"  部分匹配 (PARTIAL): {partial}")
print(f"  不匹配 (MISMATCH): {total - exact - partial}")
print(f"  准确率: {exact/total:.1%} ({exact}/{total})")
print(f"  含部分匹配准确率: {(exact+partial)/total:.1%} ({exact+partial}/{total})")
