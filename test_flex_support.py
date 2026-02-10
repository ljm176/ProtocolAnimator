"""
Test script for Flex protocol support
Tests both OT-2 and Flex protocols to verify implementation and check for regressions
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulator import ProtocolSimulator

def test_protocol(protocol_path, expected_robot='OT-2'):
    """Test a single protocol and print results"""
    print(f"\n{'='*80}")
    print(f"Testing: {Path(protocol_path).name}")
    print(f"Expected Robot: {expected_robot}")
    print('='*80)

    try:
        simulator = ProtocolSimulator(protocol_path)
        result = simulator.simulate()

        if not result['success']:
            print(f"[FAIL] {result['error']}")
            return False

        robot_config = result['robot_config']
        actual_robot = robot_config.get('robotModel', 'Unknown')
        api_level = robot_config.get('apiLevel', 'Unknown')
        pipettes = robot_config.get('pipettes', [])
        modules = robot_config.get('modules', [])
        labware = robot_config.get('labware', [])
        steps = result['steps']
        deck_layout = result['deck_layout']

        print(f"\n[PASS] SUCCESS")
        print(f"\nRobot Configuration:")
        print(f"  Robot Model: {actual_robot}")
        print(f"  API Level: {api_level}")
        print(f"  Pipettes: {len(pipettes)}")
        for p in pipettes:
            print(f"    - {p['name']} ({p['channels']} channels) on {p['mount']}")
        print(f"  Modules: {len(modules)}")
        for m in modules:
            print(f"    - {m['moduleType']} in slot {m['slot']}")
        print(f"  Labware: {len(labware)}")
        for lw in labware[:5]:  # Show first 5
            print(f"    - {lw['label']} in slot {lw['slot']}")
        if len(labware) > 5:
            print(f"    ... and {len(labware) - 5} more")

        print(f"\nDeck Layout:")
        print(f"  Total Slots: {len(deck_layout.get('slots', []))}")
        print(f"  Occupied: {len(deck_layout.get('occupied', []))}")
        print(f"  Slot Labels: {', '.join(deck_layout.get('slots', [])[:8])}...")

        print(f"\nExecution Steps:")
        print(f"  Total Steps: {len(steps)}")

        # Count step types
        step_types = {}
        for step in steps:
            step_type = step.get('type', 'other')
            step_types[step_type] = step_types.get(step_type, 0) + 1

        for step_type, count in sorted(step_types.items()):
            print(f"    - {step_type}: {count}")

        # Check for Flex-specific features
        if actual_robot == 'Flex':
            print(f"\nFlex Features Detected:")
            has_coord_slots = any(slot[0].isalpha() for slot in deck_layout.get('slots', []))
            has_96ch = any(p['channels'] == 96 for p in pipettes)
            has_gripper = any(s.get('type') == 'move_labware' for s in steps)
            print(f"  + Coordinate slots (A1-D4): {has_coord_slots}")
            print(f"  + 96-channel pipettes: {has_96ch}")
            print(f"  + Gripper moves: {has_gripper}")

        # Verify expected robot type
        if actual_robot != expected_robot:
            print(f"\n[WARN]  WARNING: Expected {expected_robot} but got {actual_robot}")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Opentrons Flex Protocol Support - Test Suite")
    print("=" * 80)

    tests = [
        # OT-2 regression test
        {
            'name': 'OT-2 Regression Test',
            'path': 'examples/sample_protocol.py',
            'expected': 'OT-2'
        },
        # Sample Flex protocol
        {
            'name': 'Sample Flex Protocol',
            'path': 'examples/sample_flex_protocol.py',
            'expected': 'Flex'
        },
        # Takara Flex protocol (the one that was failing)
        {
            'name': 'Takara Flex Protocol',
            'path': 'examples/Takara_InFusionSnapAssembly_Flex.py',
            'expected': 'Flex'
        }
    ]

    results = []
    for test in tests:
        path = Path(__file__).parent / test['path']
        if not path.exists():
            print(f"\n[WARN]  Skipping {test['name']}: File not found at {path}")
            results.append(None)
            continue

        success = test_protocol(str(path), test['expected'])
        results.append(success)

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print('='*80)

    for test, result in zip(tests, results):
        if result is None:
            status = "[SKIP]  SKIPPED"
        elif result:
            status = "[PASS] PASSED"
        else:
            status = "[FAIL] FAILED"
        print(f"{status}: {test['name']}")

    # Overall result
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0 and passed > 0:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAIL] Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
