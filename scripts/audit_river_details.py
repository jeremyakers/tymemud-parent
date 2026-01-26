import sys
import os
import re

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    text = re.sub(r'[\x1b\x1d].*?[m~]', '', text)
    return text.strip()

def get_room_data(wld_dir, vnum):
    zone = vnum // 100
    wld_file = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(wld_file):
        return None
    try:
        with open(wld_file, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception:
        return None
    room_match = re.search(fr"^#{vnum}\s*\n(.*?)\n(.*?)\n~" , content, re.MULTILINE | re.DOTALL)
    if not room_match:
        return None
    name = strip_ansi(room_match.group(1).strip())
    desc = strip_ansi(room_match.group(2).strip())
    full_room_match = re.search(fr"^#{vnum}\s*\n.*?^S" , content, re.MULTILINE | re.DOTALL)
    if not full_room_match:
        return None
    block = full_room_match.group(0)
    lines = block.split('\n')
    name_tilde_pos = content.find('~', content.find(f"#{vnum}"))
    desc_start_pos = name_tilde_pos + 1
    desc_tilde_pos = content.find('~', desc_start_pos)
    flags_start_pos = desc_tilde_pos + 1
    flags_end_pos = content.find('\n', flags_start_pos + 1)
    flags_line = content[flags_start_pos:flags_end_pos].strip().split()
    sector = -1
    if len(flags_line) >= 3:
        try:
            sector = int(flags_line[2])
        except ValueError:
            pass
    exits = {}
    d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
    for dm in d_matches:
        exits[int(dm.group(1))] = int(dm.group(4))
    return {'vnum': vnum, 'name': name, 'desc': desc, 'sector': sector, 'exits': exits}

def audit_river(wld_dir, start_vnum, end_vnum, name_hint):
    current = start_vnum
    visited = set()
    path = []
    print(f"Auditing River {name_hint} ({start_vnum} -> {end_vnum})")
    while current not in visited:
        visited.add(current)
        data = get_room_data(wld_dir, current)
        if not data: break
        path.append(data)
        issues = []
        opposites = {0:2, 1:3, 2:0, 3:1, 4:5, 5:4, 6:9, 7:8, 8:7, 9:6}
        for dir_idx, dest in data['exits'].items():
            dest_data = get_room_data(wld_dir, dest)
            if dest_data:
                opp = opposites.get(dir_idx)
                if opp is not None:
                    if dest_data['exits'].get(opp) != data['vnum']:
                        issues.append(f"Connectivity: Exit {dir_idx}->{dest} not reciprocal")
            elif 46800 <= dest <= 64099:
                issues.append(f"Connectivity: Exit {dir_idx}->{dest} destination missing")
        if name_hint.lower() not in data['name'].lower():
            issues.append(f"Naming: '{data['name']}' does not contain '{name_hint}'")
        if "The vast world stretches out in every direction" in data['desc']:
            issues.append("Description: Contains generic placeholder text")
        if issues:
            print(f"VNUM: {data['vnum']} [{data['name']}]")
            for iss in issues: print(f"  - {iss}")
        if current == end_vnum: break
        next_vnum = None
        priority = [2, 0, 1, 3, 8, 9, 6, 7] # Prefer South/downstream
        for dir_idx in priority:
            if dir_idx not in data['exits']: continue
            dest = data['exits'][dir_idx]
            if dest in visited: continue
            dest_data = get_room_data(wld_dir, dest)
            if dest_data and dest_data['sector'] == 6:
                next_vnum = dest
                break
        if not next_vnum: break
        current = next_vnum
    if not path or path[-1]['vnum'] != end_vnum:
        print(f"FAILED to reach end {end_vnum}. Stopped at {path[-1]['vnum'] if path else 'start'}")

if __name__ == "__main__":
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    audit_river(wld_dir, 46905, 63893, "Erinin")
    audit_river(wld_dir, 50960, 53946, "Luan")
    audit_river(wld_dir, 53704, 63843, "Alguenya")
    audit_river(wld_dir, 53719, 53735, "Gaelin")
