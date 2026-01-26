import re
import os

wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

with open(wld469, 'r', encoding='latin-1') as f: content = f.read()

for v in [46968, 46969]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'^(#\d+\n).*?~', rf'\1`6The River Erinin`7~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)

with open(wld469, 'w', encoding='latin-1') as f: f.write(content)
print("Corrected river names for 46968, 46969")
