import re
from pathlib import Path
p = Path(r'C:/Users/futianren/.cursor/projects/c-Users-futianren-Project-Kids-TaiChi-Media-Crawler/agent-tools/151bf7fe-c785-4c04-868f-7290d754094f.txt')
s = p.read_text(encoding='utf-8', errors='ignore')
ids = re.findall(r'(?:(?:noteId|note_id|"noteId"|"note_id")\"?\s*[:=]\s*\"?)([0-9a-f]{24})', s)
ids2 = re.findall(r'/explore/([0-9a-f]{24})', s)
all_ids = []
for x in ids+ids2:
    if x not in all_ids:
        all_ids.append(x)
print('TOTAL_UNIQUE_IDS', len(all_ids))
print('IDS', all_ids[:20])
users = re.findall(r'/user/profile/([0-9a-f]{24})', s)
u=[]
for x in users:
    if x not in u:
        u.append(x)
print('USERS', u[:10])
