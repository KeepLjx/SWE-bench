from datasets import load_dataset
ds = load_dataset('SWE-bench/SWE-bench_Lite')
inst = [x for x in ds['test'] if x['instance_id'] == 'psf__requests-2317'][0]
print("=== FULL GOLD PATCH ===")
print(inst['patch'])
