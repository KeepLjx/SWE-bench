import sys
path = r"d:\workspace\QTCTest\projects\Qoder CN\SWE-bench\eval-repos\django\django\db\models\fields\__init__.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
old = "            '\"'\"'path'\"'\"': self.path,"
new = "            '\"'\"'path'\"'\"': self.path() if callable(self.path) else self.path,"
if old not in content:
    print("ERROR: old text not found")
    sys.exit(1)
content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
