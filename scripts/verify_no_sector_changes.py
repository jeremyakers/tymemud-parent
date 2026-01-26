#!/usr/bin/env python3
"""
Verify that no sector types have changed from the baseline manifest.
Exit code 0: No sector changes detected
Exit code 1: Sector changes detected (REVERT IMMEDIATELY)
"""
import os
import re
import sys

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
manifest_file = "docs/ubermap/sector_manifest_phase4_baseline.tsv"

# If baseline doesn't exist, try the original
if not os.path.exists(manifest_file):
    manifest_file = "docs/ubermap/sector_manifest_baseline.tsv"

if not os.path.exists(manifest_file):
    print("ERROR: No baseline manifest found. Run create_sector_manifest.py first.")
    sys.exit(1)

# Load baseline
baseline = {}
with open(manifest_file, 'r') as f:
    for line in f:
        if line.startswith("VNUM"): continue
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            vnum = int(parts[0])
            sector = int(parts[2])
            baseline[vnum] = sector

# Check current state
violations = []
zones = set(v // 100 for v in baseline.keys())

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file):
        continue
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 2):
        vnum = int(blocks[i])
        if vnum not in baseline:
            continue
            
        block = blocks[i+1]
        desc_end_pos = block.find('~', block.find('~') + 1)
        flags_line = block[desc_end_pos+1:].strip().split('\n')[0].split()
        current_sector = int(flags_line[2]) if len(flags_line) > 2 else -1
        
        if current_sector != baseline[vnum]:
            violations.append(f"VNUM {vnum}: Sector changed from {baseline[vnum]} to {current_sector}")

if violations:
    print("=" * 60)
    print("CRITICAL ERROR: SECTOR CHANGES DETECTED")
    print("=" * 60)
    for v in violations:
        print(v)
    print("=" * 60)
    print("IMMEDIATE ACTION REQUIRED: git restore .")
    print("=" * 60)
    sys.exit(1)
else:
    print("✓ Sector verification passed. No sector changes detected.")
    sys.exit(0)
