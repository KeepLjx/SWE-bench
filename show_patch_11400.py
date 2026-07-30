from datasets import load_dataset
ds = load_dataset('SWE-bench/SWE-bench_Lite')
inst = [x for x in ds['test'] if x['instance_id'] == 'sympy__sympy-11400'][0]
print("=== FULL GOLD PATCH ===")
print(inst['patch'])
print("\n=== FULL TEST PATCH ===")
print(inst['test_patch'])
