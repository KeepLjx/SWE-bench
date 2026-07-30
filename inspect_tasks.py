from datasets import load_dataset

ds = load_dataset('SWE-bench/SWE-bench_Lite')

# Selected 6 tasks: 2 from each repo
selected = [
    'sympy__sympy-11400',
    'sympy__sympy-12481', 
    'django__django-10914',
    'django__django-11099',
    'psf__requests-863',
    'psf__requests-2317',
]

split = ds['test']
for sid in selected:
    inst = [x for x in split if x['instance_id'] == sid][0]
    print(f"\n{'='*80}")
    print(f"INSTANCE: {inst['instance_id']}")
    print(f"REPO: {inst['repo']}")
    print(f"BASE_COMMIT: {inst['base_commit']}")
    print(f"VERSION: {inst.get('version', 'N/A')}")
    print(f"FAIL_TO_PASS: {inst.get('FAIL_TO_PASS', 'N/A')}")
    print(f"PASS_TO_PASS (len): {len(inst.get('PASS_TO_PASS', []))}")
    print(f"\n--- PROBLEM STATEMENT (first 500 chars) ---")
    print(inst['problem_statement'][:500])
    print(f"\n--- GOLD PATCH (first 500 chars) ---")
    print(inst['patch'][:500])
    print(f"\n--- TEST PATCH (first 500 chars) ---")
    tp = inst.get('test_patch', '')
    print(tp[:500] if tp else 'None')
