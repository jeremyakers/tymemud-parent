import re
import os

def strip_mud_codes(text):
    return re.sub(r'`[^`]', '', text)

def parse_wld_file(wld_path):
    rooms = {}
    if not os.path.exists(wld_path): return {}
    with open(wld_path, 'r', encoding='latin-1', errors='replace') as f:
        content = f.read()
    blocks = re.split(r'\n#(\d+)\s*\n', content)
    for i in range(1, len(blocks), 2):
        vnum = int(blocks[i])
        body = blocks[i+1]
        lines = body.splitlines()
        if not lines: continue
        name = lines[0].rstrip('~')
        j = 1
        while j < len(lines) and not lines[j].strip().startswith('~'): j += 1
        j += 1
        if j < len(lines):
            meta = lines[j].strip().split()
            try: sector = int(meta[2]) if len(meta) >= 3 else -1
            except: sector = -1
            rooms[vnum] = {'name': name, 'sector': sector}
    return rooms

wld_dir = "_agent_work/ubermap_agent/MM32/lib/world/wld"
rooms = parse_wld_file(f"{wld_dir}/539.wld")
for v in sorted(rooms.keys()):
    r = rooms[v]
    if r['sector'] == 6:
        print(f"{v}\t{r['sector']}\t{r['name']}")
