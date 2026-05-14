import json
from pathlib import Path

p = Path('.tmp_gh_artifacts_25719121725/xhs/jsonl/creator_contents_2026-05-12.jsonl')
lines = p.read_text(encoding='utf-8').splitlines()
print('TOTAL', len(lines))
for i, l in enumerate(lines[:3], 1):
    obj = json.loads(l)
    print(f'--- SAMPLE {i} ---')
    print(json.dumps(obj, ensure_ascii=False, indent=2))
