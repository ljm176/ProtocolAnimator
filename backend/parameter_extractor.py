"""
Runtime Parameter Extraction for Opentrons Protocols.
Uses a mock ParameterContext to capture parameter definitions from
the add_parameters() function without running the full simulation.
"""
from typing import Dict, List, Any, Optional


class MockParameterContext:
    """
    Mock of opentrons.protocol_api.ParameterContext that records
    parameter definitions instead of actually registering them.
    """

    def __init__(self):
        self.parameters: List[Dict[str, Any]] = []

    def add_int(
        self,
        *,
        display_name: str,
        variable_name: str,
        default: int,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        choices: Optional[List[Dict]] = None,
    ):
        self.parameters.append({
            "type": "int",
            "display_name": display_name,
            "variable_name": variable_name,
            "default": default,
            "minimum": minimum,
            "maximum": maximum,
            "unit": unit,
            "description": description,
            "choices": choices,
        })

    def add_float(
        self,
        *,
        display_name: str,
        variable_name: str,
        default: float,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        choices: Optional[List[Dict]] = None,
    ):
        self.parameters.append({
            "type": "float",
            "display_name": display_name,
            "variable_name": variable_name,
            "default": default,
            "minimum": minimum,
            "maximum": maximum,
            "unit": unit,
            "description": description,
            "choices": choices,
        })

    def add_bool(
        self,
        *,
        display_name: str,
        variable_name: str,
        default: bool,
        description: Optional[str] = None,
    ):
        self.parameters.append({
            "type": "bool",
            "display_name": display_name,
            "variable_name": variable_name,
            "default": default,
            "description": description,
        })

    def add_str(
        self,
        *,
        display_name: str,
        variable_name: str,
        default: str,
        description: Optional[str] = None,
        choices: Optional[List[Dict]] = None,
    ):
        self.parameters.append({
            "type": "str",
            "display_name": display_name,
            "variable_name": variable_name,
            "default": default,
            "description": description,
            "choices": choices,
        })

    def add_csv_file(
        self,
        *,
        display_name: str,
        variable_name: str,
        description: Optional[str] = None,
    ):
        self.parameters.append({
            "type": "csv_file",
            "display_name": display_name,
            "variable_name": variable_name,
            "default": None,
            "description": description,
        })


def extract_parameters(protocol_code: str) -> Dict[str, Any]:
    """
    Parse protocol code and extract runtime parameter definitions.

    Executes the protocol module to find `add_parameters`, then calls it
    with a MockParameterContext to capture the definitions.

    Returns:
        {"has_parameters": bool, "parameters": [...]}
    """
    try:
        exec_globals: Dict[str, Any] = {"__name__": "__main__"}
        exec(protocol_code, exec_globals)

        if "add_parameters" not in exec_globals:
            return {"has_parameters": False, "parameters": []}

        mock_ctx = MockParameterContext()
        exec_globals["add_parameters"](mock_ctx)

        return {
            "has_parameters": len(mock_ctx.parameters) > 0,
            "parameters": mock_ctx.parameters,
        }
    except Exception as e:
        return {
            "has_parameters": False,
            "parameters": [],
            "error": str(e),
        }
