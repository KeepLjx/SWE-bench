"""Extract full details for the 6 selected instances."""
from datasets import load_dataset
import json
import os

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

ds = load_dataset('SWE-bench/SWE-bench_Lite', split='test')

instance_ids = [
    'sympy__sympy-11400',
    'sympy__sympy-11870',
    'django__django-10914',
    'django__django-10924',
    'psf__requests-1963',
    'psf__requests-2148',
]

output_dir = 'instance_details'
os.makedirs(output_dir, exist_ok=True)

summary = []

for instance_id in instance_ids:
    inst = None
    for i in ds:
        if i['instance_id'] == instance_id:
            inst = i
            break
    
    if inst is None:
        print(f"ERROR: {instance_id} not found!")
        continue
    
    fail_to_pass = json.loads(inst['FAIL_TO_PASS']) if isinstance(inst['FAIL_TO_PASS'], str) else inst['FAIL_TO_PASS']
    pass_to_pass = json.loads(inst['PASS_TO_PASS']) if isinstance(inst['PASS_TO_PASS'], str) else inst['PASS_TO_PASS']
    
    details = {
        'instance_id': inst['instance_id'],
        'repo': inst['repo'],
        'base_commit': inst['base_commit'],
        'problem_statement': inst['problem_statement'],
        'hints_text': inst.get('hints_text', ''),
        'FAIL_TO_PASS': fail_to_pass,
        'PASS_TO_PASS': pass_to_pass,
        'patch': inst['patch'],  # gold patch
        'test_patch': inst.get('test_patch', ''),
        'version': inst.get('version', ''),
        'created_at': inst.get('created_at', ''),
    }
    
    # Save individual file
    safe_id = instance_id.replace('/', '_').replace('__', '_')
    with open(os.path.join(output_dir, f'{safe_id}.json'), 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=2, ensure_ascii=False)
    
    summary.append({
        'instance_id': instance_id,
        'repo': inst['repo'],
        'base_commit': inst['base_commit'],
        'FAIL_TO_PASS_count': len(fail_to_pass),
        'PASS_TO_PASS_count': len(pass_to_pass),
        'patch_lines': len(inst['patch'].split('\n')),
        'problem_chars': len(inst['problem_statement']),
    })
    
    print(f"[OK] {instance_id}")
    print(f"     repo: {inst['repo']}")
    print(f"     base_commit: {inst['base_commit']}")
    print(f"     FAIL_TO_PASS ({len(fail_to_pass)}): {fail_to_pass}")
    print(f"     PASS_TO_PASS ({len(pass_to_pass)}): {len(pass_to_pass)} tests")
    print(f"     problem_statement: {len(inst['problem_statement'])} chars")
    print(f"     patch: {len(inst['patch'].split(chr(10)))} lines")
    print()

# Save summary
with open(os.path.join(output_dir, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"\nDetails saved to {output_dir}/")
print(json.dumps(summary, indent=2, ensure_ascii=False))
