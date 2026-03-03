"""
Protocol Animator Core
Simulates Opentrons API v2 protocols and extracts configuration, deck layout, and steps.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from io import StringIO
import sys
from opentrons.simulate import simulate as _ot_simulate, get_protocol_api


class _MockCSVParameter:
    """
    Mimics opentrons CSVParameter so that protocol.params.<csv_var>.parse_as_csv()
    and .contents work during simulation.

    parse_as_csv() returns list[list[str]] (rows including header), matching the
    real Opentrons API. Protocols typically do:
        data = protocol.params.my_csv.parse_as_csv()
        for row in data[1:]:  # skip header
            slot, well, volume = row[0], row[1], float(row[2])
    """

    def __init__(self, contents: str):
        self.contents = contents
        self.file = __import__('io').StringIO(contents)

    def parse_as_csv(self, **kwargs):
        import csv
        from io import StringIO
        reader = csv.reader(StringIO(self.contents), **kwargs)
        return list(reader)


class ProtocolSimulator:
    """Simulates an Opentrons protocol and extracts structured data."""

    # Standard labware substitutes for unknown labware
    LABWARE_SUBSTITUTES = {
        '96': 'opentrons_96_wellplate_200ul_pcr_full_skirt',
        '384': 'corning_384_wellplate_112ul_flat',
    }

    def __init__(self, protocol_path: str, metadata: Optional[Dict] = None, param_values: Optional[Dict] = None, csv_data: Optional[Dict] = None, labware_overrides: Optional[Dict] = None):
        self.protocol_path = Path(protocol_path)
        self.metadata = metadata or {}
        self.param_values = param_values or {}
        self.csv_data = csv_data or {}  # {variable_name: csv_string}
        self.labware_overrides = labware_overrides or {}  # {unknown_load_name: standard_load_name}
        self.robot_config = {}
        self.steps = []
        self.deck_layout = {}
        self.robot_model = 'OT-2'  # Default to OT-2

    def simulate(self) -> Dict[str, Any]:
        """
        Run the protocol simulation and return all extracted data.

        Returns:
            Dict containing robot_config, steps, deck_layout, and metadata
        """
        try:
            import re

            # Read protocol file
            with open(self.protocol_path, 'r') as f:
                protocol_code = f.read()

            # Extract metadata from protocol code
            protocol_metadata = self._extract_metadata(protocol_code)
            if protocol_metadata:
                self.metadata.update(protocol_metadata)

            # Extract requirements (for Flex detection)
            protocol_requirements = self._extract_requirements(protocol_code)
            self.robot_model = self._detect_robot_model(protocol_requirements)

            # Get API level from requirements first (Flex protocols), then metadata (OT-2), with fallback
            api_level = protocol_requirements.get('apiLevel') or protocol_metadata.get('apiLevel', '2.14')

            # If user provided parameter overrides, rewrite defaults in the source
            # so opentrons.simulate() picks up the custom values in its runlog
            sim_code = protocol_code
            if self.param_values and 'def add_parameters(' in protocol_code:
                sim_code = self._rewrite_defaults(protocol_code, self.param_values)

            # If CSV data is provided, rewrite the source to strip csv_file params
            # and inject the data directly. opentrons.simulate.simulate() has no way
            # to pass CSV files, so we must remove them from the parameter definitions
            # and provide the data through a module-level mock object instead.
            if self.csv_data and 'add_csv_file' in sim_code:
                sim_code = self._rewrite_csv_params(sim_code, self.csv_data)

            # If labware overrides are provided, rewrite load_labware() calls
            if self.labware_overrides:
                sim_code = self._rewrite_labware_names(sim_code, self.labware_overrides)

            # Run simulation to get runlog
            runlog, bundle = _ot_simulate(
                StringIO(sim_code),
                file_name=self.protocol_path.name,
                log_level='info'
            )

            # Execute protocol to get context with actual loaded labware/instruments
            # Pass robot_type to create the correct context (Flex or OT-2)
            protocol_context = get_protocol_api(api_level, robot_type=self.robot_model)

            # Create a safe execution environment
            exec_globals = {
                'metadata': protocol_metadata,
                '__name__': '__main__'
            }

            # Execute the (potentially rewritten) protocol code
            exec(sim_code, exec_globals)

            # Inject runtime parameter values into the protocol context
            if 'add_parameters' in exec_globals:
                self._inject_runtime_params(exec_globals, protocol_context)

            # Run the protocol's run() function if it exists
            if 'run' in exec_globals:
                exec_globals['run'](protocol_context)

            # Extract data from executed context
            self._extract_robot_config(protocol_context, self.robot_model, api_level)
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
            error_str = str(e)
            error_detail = traceback.format_exc()

            # Detect unknown labware errors and return them separately
            unknown_labware = self._detect_unknown_labware(error_str)
            if unknown_labware:
                return {
                    'robot_config': {},
                    'steps': [],
                    'deck_layout': {},
                    'success': False,
                    'error': error_str,
                    'unknown_labware': unknown_labware,
                }

            return {
                'robot_config': {},
                'steps': [],
                'deck_layout': {},
                'success': False,
                'error': f"{error_str}\n\nDetails:\n{error_detail}"
            }

    def _detect_unknown_labware(self, error_str: str) -> Optional[List[str]]:
        """Parse simulation error to extract unknown labware load names."""
        import re
        names = set()
        # Pattern: 'Labware "X" not found'
        for m in re.finditer(r'Labware "([^"]+)" not found', error_str):
            names.add(m.group(1))
        # Pattern: 'Unable to find a labware...definition for "X"'
        for m in re.finditer(r'Unable to find a labware\s+definition for "([^"]+)"', error_str):
            names.add(m.group(1))
        return list(names) if names else None

    def _rewrite_labware_names(self, code: str, overrides: Dict[str, str]) -> str:
        """
        Rewrite protocol source to substitute unknown labware load names
        with known standard ones in load_labware() calls.
        The label argument is preserved so the user sees their original name.
        """
        import re
        modified = code
        for unknown_name, substitute_name in overrides.items():
            pattern = r"""(load_labware\s*\(\s*)(['"]){name}(['"])""".format(
                name=re.escape(unknown_name)
            )
            def make_replacer(sub):
                def replacer(m):
                    return m.group(1) + m.group(2) + sub + m.group(3)
                return replacer
            modified = re.sub(pattern, make_replacer(substitute_name), modified)
        return modified

    def _extract_robot_config(self, protocol: Any, robot_model: str = 'OT-2', api_level: str = '2.x') -> None:
        """Extract pipettes, modules, and labware from the protocol context."""
        self.robot_config = {
            'robotModel': robot_model,
            'apiLevel': api_level,
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
                            slot_match = re.search(r'on\s+(?:slot\s+)?([A-D]?\d+)', module_str)
                            module_slot = slot_match.group(1) if slot_match else slot

                            slot = module_slot
                            parent = f"{model_name}:{module_slot}"
                        elif hasattr(parent_obj, 'load_name'):
                            # It's an adapter - extract slot from adapter's parent
                            adapter_name = parent_obj.load_name if hasattr(parent_obj, 'load_name') else 'adapter'
                            # Get adapter's slot
                            if hasattr(parent_obj, 'parent'):
                                adapter_parent = parent_obj.parent
                                if isinstance(adapter_parent, str) or isinstance(adapter_parent, int):
                                    slot = str(adapter_parent)
                                    parent = f"{adapter_name}:{slot}"

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
            step = self._normalize_command(idx, log_entry, self.robot_config)
            if step:
                self.steps.append(step)

    def _normalize_command(self, idx: int, log_entry: Dict, robot_config: Dict = None) -> Optional[Dict]:
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

        # Try to extract well and labware info for source/dest
        well = None
        labware = None
        import re

        def _resolve_labware_by_slot(slot_num: str) -> Optional[str]:
            if not robot_config or 'labware' not in robot_config:
                return None
            for lw in robot_config['labware']:
                if str(lw.get('slot')) == str(slot_num):
                    return lw.get('label', lw.get('loadName'))
            return None

        def _normalize_labware_text(value: Optional[str]) -> str:
            if not value:
                return ''
            return re.sub(r'[^a-z0-9]+', '', value.lower())

        def _resolve_labware_by_text(labware_text: str) -> Optional[str]:
            if not robot_config or 'labware' not in robot_config:
                return None
            target = _normalize_labware_text(labware_text)
            if not target:
                return None
            for lw in robot_config['labware']:
                label = _normalize_labware_text(lw.get('label', ''))
                load = _normalize_labware_text(lw.get('loadName', ''))
                if label and label in target:
                    return lw.get('label', lw.get('loadName'))
                if load and load in target:
                    return lw.get('label', lw.get('loadName'))
            return None

        if 'location' in payload:
            location = payload['location']

            # APPROACH 1: Try to get from location object (most reliable for matching well_coordinates)
            if hasattr(location, 'labware') and location.labware:
                labware_or_well = location.labware

                # Check if it's a string (well ID like "A1")
                if isinstance(labware_or_well, str):
                    well = labware_or_well
                else:
                    # It's a Well object
                    if hasattr(labware_or_well, 'well_name'):
                        well = labware_or_well.well_name
                    elif hasattr(labware_or_well, 'display_name'):
                        well = labware_or_well.display_name.split()[0] if labware_or_well.display_name else None

                    # Get parent labware from Well object - USE .name to match well_coordinates
                    if hasattr(labware_or_well, 'parent'):
                        labware_obj = labware_or_well.parent
                        if hasattr(labware_obj, 'name'):
                            labware = labware_obj.name

        # APPROACH 2: Parse from text as fallback (well, labware, AND slot)
        # This runs even if there's no location in payload
        if text and (not well or not labware):
            # Pattern: "from/to/into WELL of LABWARE on [slot] N"
            # Example: "Dispensing 100.0 uL into A2 of Corning 96 Well Plate 360 µL Flat on 1"
            # Note: Some API versions say "on slot N", others just "on N"
            # Supports both numeric (OT-2) and coordinate (Flex) slots
            pattern = r'(?:from|to|into)\s+([A-H]\d{1,2})\s+of\s+(.+?)\s+on\s+(?:slot\s+)?([A-D]?\d+)'
            match = re.search(pattern, text)
            if match:
                if not well:
                    well = match.group(1).strip()
                if not labware:
                    slot_num = match.group(3).strip()
                    # Look up which labware is in this slot from robot_config
                    if robot_config and 'labware' in robot_config:
                        for lw in robot_config['labware']:
                            if str(lw.get('slot')) == slot_num:
                                # Found it! Use the labware name (label matches well_coordinates keys)
                                labware = lw.get('label', lw.get('loadName'))
                                break

        text_lower = text.lower()
        is_distribute_transfer = 'distributing' in text_lower or 'distribute' in text_lower or 'transferring' in text_lower or 'transfer' in text_lower

        if text and is_distribute_transfer:
            def _extract_end_well(patterns: List[str]) -> Optional[Dict[str, str]]:
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if not match:
                        continue
                    well_id = match.group(1).strip()
                    labware_text = match.group(2).strip()
                    slot = match.group(3).strip() if match.lastindex and match.lastindex >= 3 else None
                    if slot:
                        labware_name = _resolve_labware_by_slot(slot)
                    else:
                        labware_name = _resolve_labware_by_text(labware_text)
                    if labware_name:
                        return {'labware': labware_name, 'well': well_id}
                return None

            source_patterns = [
                r'from\s+([A-H]\d{1,2})\s+of\s+(.+?)\s+on\s+(?:slot\s+)?([A-D]?\d+)',
                r'from\s+([A-H]\d{1,2})\s+of\s+(.+?)(?:\s+to\b|$)'
            ]
            dest_patterns = [
                r'\bto\s+([A-H]\d{1,2})\s+of\s+(.+?)\s+on\s+(?:slot\s+)?([A-D]?\d+)',
                r'\bto\s+([A-H]\d{1,2})\s+of\s+(.+?)(?:$)'
            ]

            if 'source' not in step:
                source_data = _extract_end_well(source_patterns)
                if source_data:
                    step['source'] = source_data

            if 'dest' not in step:
                dest_data = _extract_end_well(dest_patterns)
                if dest_data:
                    step['dest'] = dest_data

        # Store if we found both
        if not is_distribute_transfer and well and labware:
            # Determine if source or destination based on command type
            if 'Aspirating' in text or 'Picking up' in text:
                step['source'] = {'labware': labware, 'well': well}
            elif 'Dispensing' in text or 'Dropping' in text:
                step['dest'] = {'labware': labware, 'well': well}

        if 'rate' in payload:
            step['flowRateUlS'] = payload.get('volume', 0) * payload['rate'] if 'volume' in payload else None

        # Determine step type from text
        if 'aspirating' in text_lower or 'aspirate' in text_lower:
            step['type'] = 'aspirate'
        elif 'dispensing' in text_lower or 'dispense' in text_lower:
            step['type'] = 'dispense'
        elif 'picking up tip' in text_lower:
            step['type'] = 'pick_up_tip'
        elif 'dropping tip' in text_lower or 'drop tip' in text_lower:
            step['type'] = 'drop_tip'
        elif 'distributing' in text_lower or 'distribute' in text_lower:
            step['type'] = 'distribute'
        elif 'transferring' in text_lower or 'transfer' in text_lower:
            step['type'] = 'transfer'
        elif 'mixing' in text_lower or 'mix' in text_lower:
            step['type'] = 'mix'
        elif 'temperature' in text_lower or 'temp' in text_lower:
            step['type'] = 'module.set_temperature'
            # Try to extract temperature value
            import re
            temp_match = re.search(r'(\d+(?:\.\d+)?)\s*°?C', text)
            if temp_match:
                step['targetC'] = float(temp_match.group(1))
        elif 'moving' in text_lower or 'move_labware' in text_lower or 'gripper' in text_lower:
            step['type'] = 'move_labware'
            # Parse source and dest slots
            # Pattern: "moving labware from slot X to slot Y"
            # Supports both numeric (OT-2) and coordinate (Flex) slots
            move_pattern = r'from\s+(?:slot\s+)?([A-D]?\d+)\s+to\s+(?:slot\s+)?([A-D]?\d+)'
            match = re.search(move_pattern, text)
            if match:
                step['sourceSlot'] = match.group(1)
                step['destSlot'] = match.group(2)
            # Detect gripper usage
            step['useGripper'] = 'gripper' in text_lower

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

    def _extract_requirements(self, protocol_code: str) -> Dict[str, Any]:
        """Extract requirements dictionary from protocol code."""
        import re
        import ast

        requirements = {}

        # Try to find requirements dictionary in the code
        # Pattern: requirements = {...}
        requirements_pattern = r'requirements\s*=\s*(\{[^}]+\})'
        match = re.search(requirements_pattern, protocol_code, re.DOTALL)

        if match:
            try:
                # Safely evaluate the dictionary
                requirements_str = match.group(1)
                requirements = ast.literal_eval(requirements_str)
            except:
                pass

        return requirements

    def _detect_robot_model(self, requirements: Dict[str, Any]) -> str:
        """Detect robot model from requirements."""
        robot_type = requirements.get('robotType', '').lower()
        if robot_type == 'flex':
            return 'Flex'
        return 'OT-2'

    def _rewrite_defaults(self, code: str, param_values: Dict[str, Any]) -> str:
        """
        Rewrite default values in add_parameters() calls so that
        opentrons.simulate.simulate() picks up user-specified values.
        """
        import re
        modified = code
        for var_name, value in param_values.items():
            # Match: variable_name="var_name" ... default=VALUE within a parameter call
            pattern = (
                r'(variable_name\s*=\s*["\']'
                + re.escape(var_name)
                + r'["\'][^)]*?default\s*=\s*)'
                r'([^,\)]+)'
            )
            modified = re.sub(
                pattern,
                lambda m: m.group(1) + repr(value),
                modified,
                count=1,
                flags=re.DOTALL,
            )
        return modified

    def _rewrite_csv_params(self, code: str, csv_data: Dict[str, str]) -> str:
        """
        Rewrite protocol source to remove csv_file parameters from add_parameters()
        and inject the CSV data as module-level mock objects.

        opentrons.simulate.simulate() cannot accept CSV file data, so we:
        1. Remove parameters.add_csv_file(...) calls from the source
        2. Inject a lightweight mock class + instances at the top of the file
        3. Patch protocol.params.<var> access in run() to use the injected data

        The mock is injected by wrapping the run() function so that
        protocol.params.<csv_var> resolves to our mock before the real
        runtime-parameter system complains.
        """
        import re

        modified = code

        # Step 1: Remove add_csv_file() calls from add_parameters body
        for var_name in csv_data:
            # Match the full parameters.add_csv_file(...) call for this variable
            # Use [ \t]* (not \s*) after the closing paren to avoid eating
            # the indentation of the next line
            pattern = (
                r'[ \t]*parameters\.add_csv_file\s*\([^)]*variable_name\s*=\s*["\']'
                + re.escape(var_name)
                + r'["\'][^)]*\)[ \t]*\n?'
            )
            modified = re.sub(pattern, '', modified, count=1, flags=re.DOTALL)

        # Step 2: Build a preamble that provides the CSV data as mock objects
        preamble_lines = [
            '# --- Injected CSV mock for simulation ---',
            'import csv as _csv, io as _io',
            'class _InjectedCSV:',
            '    def __init__(self, _c):',
            '        self.contents = _c',
            '        self.file = _io.StringIO(_c)',
            '    def parse_as_csv(self, **kw):',
            '        return list(_csv.reader(_io.StringIO(self.contents), **kw))',
        ]
        for var_name, contents in csv_data.items():
            preamble_lines.append(
                f'_injected_csv_{var_name} = _InjectedCSV({repr(contents)})'
            )
        preamble_lines.append('# --- End injected CSV mock ---')
        preamble = '\n'.join(preamble_lines) + '\n'

        # Insert preamble after the imports (before first def/class or metadata/requirements)
        # Find a safe insertion point: after the last top-level import or module docstring
        insert_match = re.search(
            r'^(from\s+\S+\s+import\s+.*|import\s+\S+.*)\n',
            modified,
            re.MULTILINE,
        )
        if insert_match:
            insert_pos = insert_match.end()
            modified = modified[:insert_pos] + '\n' + preamble + '\n' + modified[insert_pos:]
        else:
            modified = preamble + '\n' + modified

        # Step 3: Wrap run() to patch protocol.params with our CSV mocks
        # We inject setattr calls at the very start of run()
        patch_lines = []
        for var_name in csv_data:
            patch_lines.append(
                f'    try:\n'
                f'        setattr(protocol.params, "{var_name}", _injected_csv_{var_name})\n'
                f'    except Exception:\n'
                f'        pass'
            )
        patch_block = '\n'.join(patch_lines) + '\n'

        # Insert the patch right after "def run(protocol...):" line
        run_pattern = r'(def\s+run\s*\([^)]*\)\s*:\s*\n)'
        modified = re.sub(
            run_pattern,
            lambda m: m.group(1) + patch_block,
            modified,
            count=1,
        )

        return modified

    def _inject_runtime_params(self, exec_globals: Dict, protocol_context: Any) -> None:
        """
        Inject runtime parameter values into the protocol context so that
        protocol.params.<variable_name> returns the user-specified value.
        """
        import types
        import csv as csv_mod
        from io import StringIO as SIO
        from parameter_extractor import MockParameterContext

        try:
            # Discover parameter definitions using the mock context
            mock_ctx = MockParameterContext()
            exec_globals['add_parameters'](mock_ctx)

            # Build a namespace with defaults, then apply user overrides
            param_attrs = {}
            for param_def in mock_ctx.parameters:
                vname = param_def['variable_name']
                if param_def['type'] == 'csv_file':
                    # Create a mock CSV parameter object
                    csv_contents = self.csv_data.get(vname, '')
                    param_attrs[vname] = _MockCSVParameter(csv_contents)
                else:
                    param_attrs[vname] = param_def['default']

            # Apply user-provided overrides for primitive params
            for vname, value in self.param_values.items():
                if vname in param_attrs and not isinstance(param_attrs[vname], _MockCSVParameter):
                    param_attrs[vname] = value

            # Create a simple namespace that protocol.params will return
            params_ns = types.SimpleNamespace(**param_attrs)

            # Monkey-patch onto the protocol context
            # Works for both OT-2 and Flex contexts
            protocol_context._params = params_ns
        except Exception as e:
            import traceback
            print(f"Warning: Could not inject runtime parameters: {traceback.format_exc()}")

    def _extract_deck_layout(self, protocol: Any) -> None:
        """Extract deck layout information for visualization."""
        deck_config = build_deck_config(self.robot_model)
        self.deck_layout = {
            'slots': deck_config['slotLabels'],
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
                       rows: int, cols: int, well_color: str, is_tiprack: bool = False,
                       is_reservoir: bool = False) -> str:
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

    # For tipracks/reservoirs, use slightly different styling
    if is_tiprack:
        stroke_width = 1.0
        fill_opacity = 0.4
    elif is_reservoir:
        stroke_width = 1.0
        fill_opacity = 0.2
    else:
        stroke_width = 0.7
        fill_opacity = 0.15

    for row in range(rows):
        for col in range(cols):
            if is_reservoir:
                rect_x = x + padding_x + col * cell_width + 1
                rect_y = y + padding_top + row * cell_height + 1
                rect_w = max(cell_width - 2, 1)
                rect_h = max(cell_height - 2, 1)
                svg += f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{rect_w:.1f}" height="{rect_h:.1f}" '
                svg += f'fill="{well_color}" fill-opacity="{fill_opacity}" '
                svg += f'stroke="{well_color}" stroke-width="{stroke_width}" rx="3"/>'
            else:
                cx = x + padding_x + (col + 0.5) * cell_width
                cy = y + padding_top + (row + 0.5) * cell_height

                svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                svg += f'fill="{well_color}" fill-opacity="{fill_opacity}" '
                svg += f'stroke="{well_color}" stroke-width="{stroke_width}"/>'

    return svg


def build_deck_config(robot_model: str) -> Dict:
    """
    Build deck configuration for the given robot model.
    Returns all layout constants needed for SVG generation and coordinate mapping.
    """
    if robot_model == 'Flex':
        return {
            'robotModel': 'Flex',
            'slotCount': 16,
            'gridRows': 4,
            'gridCols': 4,
            'slotWidth': 170,
            'slotHeight': 120,
            'margin': 50,
            'svgWidth': 860,
            'svgHeight': 580,
            'slotLabels': ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4',
                           'C1', 'C2', 'C3', 'C4', 'D1', 'D2', 'D3', 'D4'],
            'slotNamingScheme': 'coordinate',
            'trashSlot': None,
            'trashType': 'waste_chute',
            'stagingGap': 20,
            'stagingCols': [4],
            'mainCols': 3
        }
    else:  # OT-2
        return {
            'robotModel': 'OT-2',
            'slotCount': 12,
            'gridRows': 4,
            'gridCols': 3,
            'slotWidth': 200,
            'slotHeight': 120,
            'margin': 50,
            'svgWidth': 800,
            'svgHeight': 600,
            'slotLabels': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
            'slotNamingScheme': 'numeric',
            'trashSlot': '12',
            'trashType': 'fixed_trash',
            'stagingGap': 0,
            'stagingCols': []
        }


def generate_deck_svg(robot_config: Dict) -> str:
    """Generate SVG representation of the deck layout with well patterns."""
    # Simple SVG grid for 12 slots (OT-2)
    svg = '''<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="600" fill="#0a0d0a"/>
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
        fill_color = "#131a13"
        stroke_color = "#2d5e2d"
        label_text = None
        well_format = None
        is_tiprack = False
        is_reservoir = False
        load_name = ''

        if has_module:
            # Module slot - warm phosphor
            fill_color = "#0d1f0d"
            stroke_color = "#c8a000"
            label_text = modules[slot_str].get('model', 'Module')
            # Check for nested labware on module
            if slot_labware:
                nested_lw = slot_labware[0]
                load_name = nested_lw.get('loadName', '').lower()
                well_format = _detect_well_format(load_name)
                is_tiprack = 'tiprack' in load_name or 'tip_rack' in load_name
                is_reservoir = 'reservoir' in load_name
        elif slot_labware:
            lw = slot_labware[0]  # Primary labware in slot
            load_name = lw.get('loadName', '').lower()
            label_text = lw.get('label', lw.get('loadName', 'Unknown'))
            well_format = _detect_well_format(load_name)
            is_reservoir = 'reservoir' in load_name

            if 'tiprack' in load_name or 'tip_rack' in load_name:
                # Tiprack - matrix green
                fill_color = "#0d1a0d"
                stroke_color = "#00ff41"
                is_tiprack = True
            elif 'trash' in load_name:
                # Trash - alarm red
                fill_color = "#1a0d0d"
                stroke_color = "#ff3b30"
            else:
                # Regular labware - dim green
                fill_color = "#111a11"
                stroke_color = "#4a8a4a"

        # Draw slot background
        svg += f'<rect x="{x}" y="{y}" width="{slot_width-10}" height="{slot_height-10}" '
        svg += f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" rx="5"/>'

        # Draw well pattern if applicable
        if well_format and 'trash' not in load_name:
            rows, cols = well_format
            svg += _draw_well_pattern(
                x, y, slot_width - 10, slot_height - 10,
                rows, cols, stroke_color, is_tiprack, is_reservoir
            )

        # Slot number (positioned at top-left)
        svg += f'<text x="{x+5}" y="{y+12}" font-size="10" font-weight="bold" fill="{stroke_color}">Slot {slot_num}</text>'

        # Labware/module label at bottom
        if label_text:
            # Truncate long labels
            display_label = label_text[:22] + '..' if len(label_text) > 22 else label_text
            svg += f'<text x="{x+5}" y="{y+slot_height-15}" font-size="9" fill="#7bc47b">{display_label}</text>'

    svg += '</svg>'
    return svg


def generate_flex_deck_svg(robot_config: Dict) -> str:
    """Generate SVG representation of the Flex deck layout (4×4 grid) with well patterns."""
    deck_config = build_deck_config('Flex')

    slot_width = deck_config['slotWidth']
    slot_height = deck_config['slotHeight']
    margin = deck_config['margin']
    staging_gap = deck_config['stagingGap']
    svg_width = deck_config['svgWidth']
    svg_height = deck_config['svgHeight']

    svg = f'''<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="{svg_width}" height="{svg_height}" fill="#0a0d0a"/>
    '''

    # Add row headers (A-D) on the left
    for row in range(4):
        row_letter = chr(ord('A') + row)
        y = margin + row * slot_height + slot_height / 2
        svg += f'<text x="{margin - 20}" y="{y + 5}" font-size="14" font-weight="bold" fill="#7bc47b" text-anchor="middle">{row_letter}</text>'

    # Add column headers (1-4) on top
    for col in range(4):
        col_number = col + 1
        extra_gap = staging_gap if col == 3 else 0
        x = margin + col * slot_width + extra_gap + slot_width / 2
        svg += f'<text x="{x}" y="{margin - 15}" font-size="14" font-weight="bold" fill="#7bc47b" text-anchor="middle">{col_number}</text>'

    # Add dashed separator line before column 4 (staging area)
    separator_x = margin + 3 * slot_width + staging_gap / 2
    svg += f'<line x1="{separator_x}" y1="{margin}" x2="{separator_x}" y2="{margin + 4 * slot_height}" stroke="#2d5e2d" stroke-width="2" stroke-dasharray="5,5"/>'

    # Add "Staging Area" label above column 4
    staging_label_x = margin + 3 * slot_width + staging_gap + slot_width / 2
    svg += f'<text x="{staging_label_x}" y="{margin - 30}" font-size="12" font-weight="bold" fill="#4a8a4a" text-anchor="middle">Staging Area</text>'

    # Build lookup for what's in each slot
    modules = {str(m['slot']): m for m in robot_config.get('modules', [])}
    labware_by_slot = {}
    for lw in robot_config.get('labware', []):
        slot = lw['slot']
        if slot not in labware_by_slot:
            labware_by_slot[slot] = []
        labware_by_slot[slot].append(lw)

    # Draw all 16 slots (4×4 grid)
    for slot_label in deck_config['slotLabels']:
        # Parse coordinate label (e.g., 'B3')
        if not slot_label or len(slot_label) < 2:
            continue  # Skip invalid slot labels

        row_letter = slot_label[0]
        try:
            col_number = int(slot_label[1:])
        except ValueError:
            continue  # Skip if slot number is invalid

        row = ord(row_letter) - ord('A')  # A=0, B=1, C=2, D=3
        col = col_number - 1  # 1=0, 2=1, 3=2, 4=3

        # Apply staging gap for column 4
        extra_gap = staging_gap if col == 3 else 0
        x = margin + col * slot_width + extra_gap
        y = margin + row * slot_height

        # Determine slot contents and color
        has_module = slot_label in modules
        slot_labware = labware_by_slot.get(slot_label, [])

        # Default empty slot
        fill_color = "#131a13"
        stroke_color = "#2d5e2d"
        label_text = None
        well_format = None
        is_tiprack = False
        is_reservoir = False
        load_name = ''

        if has_module:
            # Module slot - warm phosphor
            fill_color = "#0d1f0d"
            stroke_color = "#c8a000"
            label_text = modules[slot_label].get('model', 'Module')
            # Check for nested labware on module
            if slot_labware:
                nested_lw = slot_labware[0]
                load_name = nested_lw.get('loadName', '').lower()
                well_format = _detect_well_format(load_name)
                is_tiprack = 'tiprack' in load_name or 'tip_rack' in load_name
                is_reservoir = 'reservoir' in load_name
        elif slot_labware:
            lw = slot_labware[0]  # Primary labware in slot
            load_name = lw.get('loadName', '').lower()
            label_text = lw.get('label', lw.get('loadName', 'Unknown'))
            well_format = _detect_well_format(load_name)
            is_reservoir = 'reservoir' in load_name

            if 'tiprack' in load_name or 'tip_rack' in load_name:
                # Tiprack - matrix green
                fill_color = "#0d1a0d"
                stroke_color = "#00ff41"
                is_tiprack = True
            elif 'trash' in load_name:
                # Trash - alarm red
                fill_color = "#1a0d0d"
                stroke_color = "#ff3b30"
            else:
                # Regular labware - dim green
                fill_color = "#111a11"
                stroke_color = "#4a8a4a"

        # Draw slot background
        svg += f'<rect x="{x}" y="{y}" width="{slot_width-10}" height="{slot_height-10}" '
        svg += f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" rx="5"/>'

        # Draw well pattern if applicable
        if well_format and 'trash' not in load_name:
            rows, cols = well_format
            svg += _draw_well_pattern(
                x, y, slot_width - 10, slot_height - 10,
                rows, cols, stroke_color, is_tiprack, is_reservoir
            )

        # Slot label (positioned at top-left)
        svg += f'<text x="{x+5}" y="{y+12}" font-size="10" font-weight="bold" fill="{stroke_color}">{slot_label}</text>'

        # Labware/module label at bottom
        if label_text:
            # Truncate long labels
            display_label = label_text[:20] + '..' if len(label_text) > 20 else label_text
            svg += f'<text x="{x+5}" y="{y+slot_height-15}" font-size="9" fill="#7bc47b">{display_label}</text>'

    # Add waste chute indicator in bottom-right margin
    waste_x = margin + 4 * slot_width + staging_gap + 10
    waste_y = margin + 4 * slot_height - 40
    svg += f'<rect x="{waste_x}" y="{waste_y}" width="40" height="30" fill="#1a0d0d" stroke="#ff3b30" stroke-width="2" rx="3"/>'
    svg += f'<text x="{waste_x + 20}" y="{waste_y + 18}" font-size="8" fill="#ff3b30" text-anchor="middle">Waste</text>'
    svg += f'<text x="{waste_x + 20}" y="{waste_y + 26}" font-size="8" fill="#ff3b30" text-anchor="middle">Chute</text>'

    svg += '</svg>'
    return svg


def generate_well_coordinates(robot_config: Dict) -> Dict:
    """
    Generate SVG coordinate mapping for all wells in all labware.
    Returns: {slot: {labware_label: {well_id: {x, y}}}}
    """
    coordinates = {}

    # Deck layout constants (match generate_deck_svg)
    slot_width = 200
    slot_height = 120
    margin = 50

    # Well pattern constants (match _draw_well_pattern)
    padding_top = 18
    padding_bottom = 18
    padding_x = 20

    # Build module lookup
    modules = {str(m['slot']): m for m in robot_config.get('modules', [])}

    for labware in robot_config.get('labware', []):
        slot_str = labware['slot']
        slot_num = int(slot_str)
        label = labware.get('label', 'Unknown')
        load_name = labware.get('loadName', '').lower()

        # Skip trash
        if 'trash' in load_name:
            continue

        # Calculate slot position (same logic as generate_deck_svg)
        slot_index = slot_num - 1
        row = 3 - (slot_index // 3)  # Flip vertically
        col = slot_index % 3
        slot_x = margin + col * slot_width
        slot_y = margin + row * slot_height

        # Detect well format
        well_format = _detect_well_format(load_name)
        if not well_format:
            # Can't map wells without format
            continue

        rows, cols = well_format

        # Calculate available space (same as _draw_well_pattern)
        slot_inner_width = slot_width - 10  # Account for border
        slot_inner_height = slot_height - 10
        available_width = slot_inner_width - (padding_x * 2)
        available_height = slot_inner_height - padding_top - padding_bottom

        cell_width = available_width / cols
        cell_height = available_height / rows

        # Generate coordinates for each well
        well_coords = {}

        for row_idx in range(rows):
            for col_idx in range(cols):
                # Generate well ID (A1, A2, B1, etc.)
                row_letter = chr(ord('A') + row_idx)
                col_number = col_idx + 1
                well_id = f"{row_letter}{col_number}"

                # Calculate well center position
                well_x = slot_x + padding_x + (col_idx + 0.5) * cell_width
                well_y = slot_y + padding_top + (row_idx + 0.5) * cell_height

                well_coords[well_id] = {
                    'x': round(well_x, 2),
                    'y': round(well_y, 2)
                }

        # Store coordinates by slot and labware label
        if slot_str not in coordinates:
            coordinates[slot_str] = {}
        coordinates[slot_str][label] = well_coords

    return coordinates


def generate_flex_well_coordinates(robot_config: Dict) -> Dict:
    """
    Generate SVG coordinate mapping for all wells in all labware for Flex deck.
    Returns: {slot: {labware_label: {well_id: {x, y}}}}
    """
    coordinates = {}
    deck_config = build_deck_config('Flex')

    # Deck layout constants
    slot_width = deck_config['slotWidth']
    slot_height = deck_config['slotHeight']
    margin = deck_config['margin']
    staging_gap = deck_config['stagingGap']

    # Well pattern constants (match _draw_well_pattern)
    padding_top = 18
    padding_bottom = 18
    padding_x = 20

    # Build module lookup
    modules = {str(m['slot']): m for m in robot_config.get('modules', [])}

    for labware in robot_config.get('labware', []):
        slot_label = labware['slot']
        label = labware.get('label', 'Unknown')
        load_name = labware.get('loadName', '').lower()

        # Skip trash
        if 'trash' in load_name:
            continue

        # Parse coordinate label (e.g., 'B3')
        if not slot_label or len(slot_label) < 2:
            continue  # Skip invalid slot labels

        row_letter = slot_label[0]
        try:
            col_number = int(slot_label[1:])
        except ValueError:
            continue  # Skip if slot number is invalid

        row = ord(row_letter) - ord('A')  # A=0, B=1, C=2, D=3
        col = col_number - 1  # 1=0, 2=1, 3=2, 4=3

        # Apply staging gap for column 4
        extra_gap = staging_gap if col == 3 else 0
        slot_x = margin + col * slot_width + extra_gap
        slot_y = margin + row * slot_height

        # Detect well format
        well_format = _detect_well_format(load_name)
        if not well_format:
            # Can't map wells without format
            continue

        rows, cols = well_format

        # Calculate available space (same as _draw_well_pattern)
        slot_inner_width = slot_width - 10  # Account for border
        slot_inner_height = slot_height - 10
        available_width = slot_inner_width - (padding_x * 2)
        available_height = slot_inner_height - padding_top - padding_bottom

        cell_width = available_width / cols
        cell_height = available_height / rows

        # Generate coordinates for each well
        well_coords = {}

        for row_idx in range(rows):
            for col_idx in range(cols):
                # Generate well ID (A1, A2, B1, etc.)
                row_letter = chr(ord('A') + row_idx)
                col_number = col_idx + 1
                well_id = f"{row_letter}{col_number}"

                # Calculate well center position
                well_x = slot_x + padding_x + (col_idx + 0.5) * cell_width
                well_y = slot_y + padding_top + (row_idx + 0.5) * cell_height

                well_coords[well_id] = {
                    'x': round(well_x, 2),
                    'y': round(well_y, 2)
                }

        # Store coordinates by slot and labware label
        if slot_label not in coordinates:
            coordinates[slot_label] = {}
        coordinates[slot_label][label] = well_coords

    return coordinates


def generate_deck_svg_for_robot(robot_config: Dict) -> str:
    """Dispatch to OT-2 or Flex SVG generator based on robot model."""
    robot_model = robot_config.get('robotModel', 'OT-2')
    if robot_model == 'Flex':
        return generate_flex_deck_svg(robot_config)
    else:
        return generate_deck_svg(robot_config)


def generate_well_coordinates_for_robot(robot_config: Dict) -> Dict:
    """Dispatch to OT-2 or Flex coordinate generator based on robot model."""
    robot_model = robot_config.get('robotModel', 'OT-2')
    if robot_model == 'Flex':
        return generate_flex_well_coordinates(robot_config)
    else:
        return generate_well_coordinates(robot_config)


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
