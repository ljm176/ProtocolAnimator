#!/usr/bin/env python3
"""Quick test to verify step parsing is working correctly."""

import sys
sys.path.insert(0, 'backend')

from simulator import ProtocolSimulator

# Test with the 96wp protocol
protocol_path = 'examples/96wp_liquid.py'

print("Testing protocol parsing...")
print(f"Protocol: {protocol_path}\n")

simulator = ProtocolSimulator(protocol_path)
result = simulator.simulate()

if not result['success']:
    print(f"ERROR: {result['error']}")
    sys.exit(1)

print("[OK] Simulation successful\n")

# Check steps
steps = result['steps']
print(f"Total steps: {len(steps)}\n")

# Print first 10 steps with source/dest info
for step in steps[:10]:
    print(f"Step {step['idx']}: type={step['type']}")
    if 'source' in step:
        print(f"  source: labware='{step['source']['labware']}', well='{step['source']['well']}'")
    else:
        print(f"  source: MISSING")
    if 'dest' in step:
        print(f"  dest: labware='{step['dest']['labware']}', well='{step['dest']['well']}'")
    else:
        print(f"  dest: MISSING")
    if 'metadata' in step:
        text = step['metadata'].get('text', '')[:80]
        print(f"  text: {text}...")
    print()

# Check well coordinates
from simulator import generate_well_coordinates
well_coords = generate_well_coordinates(result['robot_config'])

print("\nWell coordinates generated for slots:")
for slot, labwares in well_coords.items():
    print(f"  Slot {slot}: {list(labwares.keys())}")

print("\n[OK] Test complete!")
