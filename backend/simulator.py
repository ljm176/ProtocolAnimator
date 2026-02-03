"""
Opentrons Protocol Simulator Core
Simulates Opentrons API v2 protocols and extracts configuration, deck layout, and steps.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from io import StringIO
import sys


class ProtocolSimulator:
    """Simulates an Opentrons protocol and extracts structured data."""

    def __init__(self, protocol_path: str, metadata: Optional[Dict] = None):
        self.protocol_path = Path(protocol_path)
        self.metadata = metadata or {}
        self.robot_config = {}
        self.steps = []
        self.deck_layout = {}

    def simulate(self) -> Dict[str, Any]:
        """
        Run the protocol simulation and return all extracted data.

        Returns:
            Dict containing robot_config, steps, deck_layout, and metadata
        """
        try:
            from opentrons.simulate import simulate, get_protocol_api
            from io import StringIO
            import re

            # Read protocol file
            with open(self.protocol_path, 'r') as f:
                protocol_code = f.read()

            # Extract metadata from protocol code
            protocol_metadata = self._extract_metadata(protocol_code)
            if protocol_metadata:
                self.metadata.update(protocol_metadata)

            # Get API level from metadata
            api_level = protocol_metadata.get('apiLevel', '2.14')

            # Run simulation to get runlog
            runlog, bundle = simulate(
                StringIO(protocol_code),
                file_name=self.protocol_path.name,
                log_level='info'
            )

            # Execute protocol to get context with actual loaded labware/instruments
            protocol_context = get_protocol_api(api_level)

            # Create a safe execution environment
            exec_globals = {
                'metadata': protocol_metadata,
                '__name__': '__main__'
            }

            # Execute the protocol code
            exec(protocol_code, exec_globals)

            # Run the protocol's run() function if it exists
            if 'run' in exec_globals:
                exec_globals['run'](protocol_context)

            # Extract data from executed context
            self._extract_robot_config(protocol_context)
            self._extract_steps(runlog)
            self._extract_deck_layout(protocol_context)

            return {
                'robot_config': self.robot_config,
                'steps': self.steps,
                'deck_layout': self.deck_layout,
                'success': True,
                'error': None
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                'robot_config': {},
                'steps': [],
                'deck_layout': {},
                'success': False,
                'error': f"{str(e)}\n\nDetails:\n{error_detail}"
            }

    def _extract_robot_config(self, protocol: Any) -> None:
        """Extract pipettes, modules, and labware from the protocol context."""
        self.robot_config = {
            'robotModel': 'OT-2',
            'apiLevel': '2.x',
            'pipettes': self._extract_pipettes(protocol),
            'modules': self._extract_modules(protocol),
            'labware': self._extract_labware(protocol),
            'metadata': self.metadata
        }

    def _extract_pipettes(self, protocol: Any) -> List[Dict]:
        """Extract pipette configuration."""
        pipettes = []
        if hasattr(protocol, 'loaded_instruments'):
            for mount, pipette in protocol.loaded_instruments.items():
                if pipette:
                    # Extract tiprack names
                    tiprack_names = []
                    if hasattr(pipette, 'tip_racks'):
                        for rack in pipette.tip_racks:
                            if hasattr(rack, 'load_name'):
                                tiprack_names.append(rack.load_name)

                    pipettes.append({
                        'mount': mount.name if hasattr(mount, 'name') else str(mount),
                        'name': pipette.name,
                        'channels': pipette.channels,
                        'minVolumeUl': pipette.min_volume,
                        'maxVolumeUl': pipette.max_volume,
                        'tiprackLoadNames': tiprack_names
                    })
        return pipettes

    def _extract_modules(self, protocol: Any) -> List[Dict]:
        """Extract module configuration."""
        modules = []
        if hasattr(protocol, 'loaded_modules'):
            # loaded_modules is a dict with slot as key
            for slot, module in protocol.loaded_modules.items():
                # Get model - it's a property in API 2.14+, might be method in older versions
                model_name = 'unknown'
                if hasattr(module, 'model'):
                    model_attr = module.model
                    model_name = model_attr if isinstance(model_attr, str) else model_attr()

                modules.append({
                    'slot': str(slot),
                    'moduleType': model_name,
                    'model': model_name,
                    'state': self._get_module_state(module)
                })
        return modules

    def _get_module_state(self, module: Any) -> Dict:
        """Get current state of a module."""
        state = {}
        if hasattr(module, 'temperature'):
            state['targetTemperatureC'] = module.temperature
            state['status'] = 'holding'
        elif hasattr(module, 'speed'):
            state['speedRpm'] = module.speed
        return state

    def _extract_labware(self, protocol: Any) -> List[Dict]:
        """Extract labware configuration including parent relationships."""
        labware_list = []
        if hasattr(protocol, 'loaded_labwares'):
            for slot_key, labware_obj in protocol.loaded_labwares.items():
                if labware_obj:
                    # Get slot and parent info
                    slot = str(slot_key)
                    parent = None

                    if hasattr(labware_obj, 'parent'):
                        parent_obj = labware_obj.parent
                        # Check if parent is a module (has model attr) or a deck slot (string/int)
                        if isinstance(parent_obj, str) or isinstance(parent_obj, int):
                            # It's directly on the deck
                            slot = str(parent_obj)
                        elif hasattr(parent_obj, 'model'):
                            # It's a module - get model name and slot
                            model_attr = parent_obj.model
                            model_name = model_attr if isinstance(model_attr, str) else model_attr()

                            # Get module slot - use string parsing as fallback
                            import re
                            module_str = str(parent_obj)
                            slot_match = re.search(r'on (\d+)', module_str)
                            module_slot = slot_match.group(1) if slot_match else slot

                            slot = module_slot
                            parent = f"{model_name}:{module_slot}"

                    labware_list.append({
                        'slot': slot,
                        'parent': parent,
                        'namespace': 'opentrons',
                        'loadName': labware_obj.load_name if hasattr(labware_obj, 'load_name') else 'unknown',
                        'version': 1,
                        'label': labware_obj.name if hasattr(labware_obj, 'name') else 'unknown'
                    })
        return labware_list

    def _extract_steps(self, runlog: List) -> None:
        """Extract and normalize protocol steps from runlog."""
        self.steps = []
        for idx, log_entry in enumerate(runlog, start=1):
            step = self._normalize_command(idx, log_entry)
            if step:
                self.steps.append(step)

    def _normalize_command(self, idx: int, log_entry: Dict) -> Optional[Dict]:
        """Normalize a single command into a step."""
        # Get payload from runlog entry
        payload = log_entry.get('payload', {})
        text = payload.get('text', '')

        # Basic step structure
        step = {
            'idx': idx,
            'type': 'other',
            'metadata': {'text': text}
        }

        # Extract structured data from payload
        if 'volume' in payload:
            step['volumeUl'] = payload['volume']

        if 'instrument' in payload:
            instrument = payload['instrument']
            if hasattr(instrument, 'name'):
                step['pipette'] = f"{instrument.mount}:{instrument.name}"

        if 'location' in payload:
            location = payload['location']
            # Try to extract well and labware info
            location_str = str(location)
            if 'of' in location_str:
                parts = location_str.split(' of ')
                if len(parts) >= 2:
                    well = parts[0].strip()
                    labware = parts[1].split(' on slot ')[0].strip() if ' on slot ' in parts[1] else parts[1].strip()

                    # Determine if source or destination based on command type
                    if 'Aspirating' in text or 'Picking up' in text:
                        step['source'] = {'labware': labware, 'well': well}
                    elif 'Dispensing' in text or 'Dropping' in text:
                        step['dest'] = {'labware': labware, 'well': well}

        if 'rate' in payload:
            step['flowRateUlS'] = payload.get('volume', 0) * payload['rate'] if 'volume' in payload else None

        # Determine step type from text
        text_lower = text.lower()
        if 'aspirating' in text_lower or 'aspirate' in text_lower:
            step['type'] = 'aspirate'
        elif 'dispensing' in text_lower or 'dispense' in text_lower:
            step['type'] = 'dispense'
        elif 'picking up tip' in text_lower:
            step['type'] = 'pick_up_tip'
        elif 'dropping tip' in text_lower or 'drop tip' in text_lower:
            step['type'] = 'drop_tip'
        elif 'mixing' in text_lower or 'mix' in text_lower:
            step['type'] = 'mix'
        elif 'temperature' in text_lower or 'temp' in text_lower:
            step['type'] = 'module.set_temperature'
            # Try to extract temperature value
            import re
            temp_match = re.search(r'(\d+(?:\.\d+)?)\s*°?C', text)
            if temp_match:
                step['targetC'] = float(temp_match.group(1))

        return step

    def _extract_metadata(self, protocol_code: str) -> Dict[str, Any]:
        """Extract metadata dictionary from protocol code."""
        import re
        import ast

        metadata = {}

        # Try to find metadata dictionary in the code
        # Pattern: metadata = {...}
        metadata_pattern = r'metadata\s*=\s*(\{[^}]+\})'
        match = re.search(metadata_pattern, protocol_code, re.DOTALL)

        if match:
            try:
                # Safely evaluate the dictionary
                metadata_str = match.group(1)
                metadata = ast.literal_eval(metadata_str)
            except:
                pass

        return metadata

    def _extract_deck_layout(self, protocol: Any) -> None:
        """Extract deck layout information for visualization."""
        self.deck_layout = {
            'slots': list(range(1, 13)),
            'occupied': []
        }

        if hasattr(protocol, 'loaded_labwares'):
            for slot_key, labware_obj in protocol.loaded_labwares.items():
                if labware_obj and hasattr(labware_obj, 'parent'):
                    # Get slot - same logic as in _extract_labware
                    slot = str(slot_key)
                    parent_obj = labware_obj.parent

                    if isinstance(parent_obj, str) or isinstance(parent_obj, int):
                        slot = str(parent_obj)
                    elif hasattr(parent_obj, 'model'):
                        # It's on a module - parse slot from string representation
                        import re
                        module_str = str(parent_obj)
                        slot_match = re.search(r'on (\d+)', module_str)
                        slot = slot_match.group(1) if slot_match else slot

                    if slot and slot != 'unknown':
                        self.deck_layout['occupied'].append({
                            'slot': slot,
                            'type': 'labware',
                            'name': labware_obj.load_name if hasattr(labware_obj, 'load_name') else 'unknown'
                        })


def _detect_well_format(load_name: str) -> tuple:
    """
    Detect well format from labware load name.
    Returns (rows, cols) or None if not a standard format.
    """
    load_name = load_name.lower()

    # Check for common formats
    if '384' in load_name:
        return (16, 24)
    elif '96' in load_name:
        return (8, 12)
    elif '48' in load_name:
        return (6, 8)
    elif '24' in load_name:
        return (4, 6)
    elif '12' in load_name and 'reservoir' in load_name:
        return (1, 12)
    elif '6' in load_name and 'well' in load_name:
        return (2, 3)
    elif 'reservoir' in load_name:
        return (1, 1)  # Single trough

    return None


def _draw_well_pattern(x: int, y: int, width: int, height: int,
                       rows: int, cols: int, well_color: str, is_tiprack: bool = False) -> str:
    """
    Generate SVG for a well/tip pattern inside a slot.
    """
    svg = ''

    # Calculate well dimensions with padding
    # Top padding for slot label, side padding for margins, bottom padding for labware name
    padding_top = 18
    padding_bottom = 18
    padding_x = 20

    available_width = width - (padding_x * 2)
    available_height = height - padding_top - padding_bottom

    # Calculate spacing
    cell_width = available_width / cols
    cell_height = available_height / rows

    # Well radius - slightly larger for better visibility
    radius = min(cell_width, cell_height) * 0.38

    # For tipracks, use slightly different styling
    if is_tiprack:
        stroke_width = 1.0
        fill_opacity = 0.4
    else:
        stroke_width = 0.7
        fill_opacity = 0.15

    for row in range(rows):
        for col in range(cols):
            cx = x + padding_x + (col + 0.5) * cell_width
            cy = y + padding_top + (row + 0.5) * cell_height

            svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
            svg += f'fill="{well_color}" fill-opacity="{fill_opacity}" '
            svg += f'stroke="{well_color}" stroke-width="{stroke_width}"/>'

    return svg


def generate_deck_svg(robot_config: Dict) -> str:
    """Generate SVG representation of the deck layout with well patterns."""
    # Simple SVG grid for 12 slots (OT-2)
    svg = '''<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="600" fill="#f5f5f5"/>
    '''

    # Draw 12 slots (3 columns x 4 rows)
    slot_width = 200
    slot_height = 120
    margin = 50

    # Build lookup for what's in each slot
    modules = {str(m['slot']): m for m in robot_config.get('modules', [])}
    labware_by_slot = {}
    for lw in robot_config.get('labware', []):
        slot = lw['slot']
        if slot not in labware_by_slot:
            labware_by_slot[slot] = []
        labware_by_slot[slot].append(lw)

    for i in range(12):
        # Flip vertically: slot 1-3 at bottom, 10-12 at top
        row = 3 - (i // 3)
        col = i % 3
        x = margin + col * slot_width
        y = margin + row * slot_height
        slot_num = i + 1
        slot_str = str(slot_num)

        # Determine slot contents and color
        has_module = slot_str in modules
        slot_labware = labware_by_slot.get(slot_str, [])

        # Default empty slot
        fill_color = "white"
        stroke_color = "#333"
        label_text = None
        well_format = None
        is_tiprack = False
        load_name = ''

        if has_module:
            # Module slot - blue
            fill_color = "#dbeafe"  # blue-100
            stroke_color = "#3b82f6"  # blue-500
            label_text = modules[slot_str].get('model', 'Module')
            # Check for nested labware on module
            if slot_labware:
                nested_lw = slot_labware[0]
                load_name = nested_lw.get('loadName', '').lower()
                well_format = _detect_well_format(load_name)
                is_tiprack = 'tiprack' in load_name or 'tip_rack' in load_name
        elif slot_labware:
            lw = slot_labware[0]  # Primary labware in slot
            load_name = lw.get('loadName', '').lower()
            label_text = lw.get('label', lw.get('loadName', 'Unknown'))
            well_format = _detect_well_format(load_name)

            if 'tiprack' in load_name or 'tip_rack' in load_name:
                # Tiprack - green
                fill_color = "#dcfce7"  # green-100
                stroke_color = "#22c55e"  # green-500
                is_tiprack = True
            elif 'trash' in load_name:
                # Trash - red/orange
                fill_color = "#fee2e2"  # red-100
                stroke_color = "#ef4444"  # red-500
            else:
                # Regular labware - gray
                fill_color = "#f3f4f6"  # gray-100
                stroke_color = "#6b7280"  # gray-500

        # Draw slot background
        svg += f'<rect x="{x}" y="{y}" width="{slot_width-10}" height="{slot_height-10}" '
        svg += f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" rx="5"/>'

        # Draw well pattern if applicable
        if well_format and 'trash' not in load_name:
            rows, cols = well_format
            svg += _draw_well_pattern(
                x, y, slot_width - 10, slot_height - 10,
                rows, cols, stroke_color, is_tiprack
            )

        # Slot number (positioned at top-left)
        svg += f'<text x="{x+5}" y="{y+12}" font-size="10" font-weight="bold" fill="{stroke_color}">Slot {slot_num}</text>'

        # Labware/module label at bottom
        if label_text:
            # Truncate long labels
            display_label = label_text[:22] + '..' if len(label_text) > 22 else label_text
            svg += f'<text x="{x+5}" y="{y+slot_height-15}" font-size="9" fill="#333">{display_label}</text>'

    svg += '</svg>'
    return svg


def generate_report(robot_config: Dict, steps: List[Dict], output_dir: Path) -> str:
    """Generate markdown report summarizing the simulation."""
    report = f"""# Protocol Simulation Report

## Protocol Information
- **Name**: {robot_config.get('metadata', {}).get('protocolName', 'N/A')}
- **Author**: {robot_config.get('metadata', {}).get('author', 'N/A')}
- **Robot**: {robot_config.get('robotModel', 'OT-2')}
- **API Level**: {robot_config.get('apiLevel', '2.x')}

## Configuration Summary
- **Pipettes**: {len(robot_config.get('pipettes', []))}
- **Modules**: {len(robot_config.get('modules', []))}
- **Labware**: {len(robot_config.get('labware', []))}
- **Total Steps**: {len(steps)}

## Artifacts
- [robot.json](./robot.json) - Robot configuration
- [steps.json](./steps.json) - Execution steps
- [deck.svg](./deck.svg) - Deck layout visualization

## Quick Stats
"""

    # Count step types
    step_types = {}
    for step in steps:
        step_type = step.get('type', 'other')
        step_types[step_type] = step_types.get(step_type, 0) + 1

    for step_type, count in step_types.items():
        report += f"- **{step_type}**: {count}\n"

    return report
