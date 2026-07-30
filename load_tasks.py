from datasets import load_dataset

ds = load_dataset('SWE-bench/SWE-bench_Lite')
print('Splits:', list(ds.keys()))
print('Test size:', len(ds['test']))
if 'dev' in ds:
    print('Dev size:', len(ds['dev']))

targets = ['sympy__sympy', 'django__django', 'psf__requests']
for split_name in ds:
    split = ds[split_name]
    for target in targets:
        filtered = [x for x in split if x['instance_id'].startswith(target)]
        print(f'\n{split_name}/{target}: {len(filtered)} instances')
        for inst in filtered:
            print(f"  {inst['instance_id']} | base_commit: {inst['base_commit'][:12]} | ver: {inst.get('version','N/A')}")
