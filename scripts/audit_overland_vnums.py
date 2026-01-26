import os
import re

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    return text.strip()

def audit_zone_vnums(wld_dir, zone_num):
    wld_file = os.path.join(wld_dir, f"{zone_num}.wld")
    if not os.path.exists(wld_file):
        return []
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Split into room blocks
    rooms = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    
    results = []
    for i in range(0, len(rooms), 2):
        vnum = int(rooms[i])
        block = rooms[i+1]
        
        # Parse name
        name_match = re.search(r"^(.*?)~", block, re.MULTILINE | re.DOTALL)
        if not name_match: continue
        name = strip_ansi(name_match.group(1))
        
        # Parse description
        desc_match = re.search(r"~.*?\n(.*?)~", block, re.MULTILINE | re.DOTALL)
        if not desc_match: continue
        desc = strip_ansi(desc_match.group(1))
        
        # Parse flags/sector
        # The line after the description tilde
        desc_end_pos = block.find('~', block.find('~') + 1)
        flags_line_match = re.search(r"^(\d+ \w+ \d+)", block[desc_end_pos+1:].strip())
        if not flags_line_match: continue
        flags = flags_line_match.group(1).split()
        sector = int(flags[2])
        
        # Skip Road (11) and River (6)
        if sector in [6, 11]: continue
        
        issues = []
        # Check for placeholder text
        if "The vast world stretches out in every direction" in desc:
            issues.append("Description: Contains placeholder text")
        
        # Check name consistency
        if sector == 2 and "road" in name.lower():
            # Check if it's "Near the road" which is allowed
            if "near the" not in name.lower() and "along the" not in name.lower():
                issues.append(f"Naming: Field (Sector 2) room named '{name}'")
        
        if len(desc) < 100:
            issues.append(f"Description: Too short ({len(desc)} chars)")
            
        if issues:
            results.append({
                'vnum': vnum,
                'name': name,
                'sector': sector,
                'issues': issues
            })
            
    return results

if __name__ == "__main__":
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]
    
    print("# Phase 2: Overland Vnums Audit Results")
    total_issues = 0
    
    for z in zones:
        zone_issues = audit_zone_vnums(wld_dir, z)
        if zone_issues:
            print(f"\n### Zone {z}")
            for iss in zone_issues:
                total_issues += 1
                print(f"VNUM: {iss['vnum']} [S:{iss['sector']}] {iss['name']}")
                for i in iss['issues']:
                    print(f"  - {i}")
    
    print(f"\n**Total Issues Found**: {total_issues}")
