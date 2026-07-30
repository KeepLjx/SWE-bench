from datasets import load_dataset
ds = load_dataset('SWE-bench/SWE-bench_Lite')
inst = [x for x in ds['test'] if x['instance_id'] == 'sympy__sympy-11400'][0]
print("=== FULL PROBLEM STATEMENT ===")
print(inst['problem_statement'])
print("\n=== HINTS ===")
print(inst.get('hints_text', 'N/A')[:2000])
