import json
from pathlib import Path

src = Path('.tmp_gh_artifacts_25719121725/xhs/jsonl/creator_contents_2026-05-12.jsonl')
out = Path('.tmp_samples_full.json')
rows = []
for l in src.read_text(encoding='utf-8').splitlines()[:3]:
    rows.append(json.loads(l))
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('written', out)
