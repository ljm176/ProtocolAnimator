"""
FastAPI backend for Opentrons Protocol Simulator
Provides REST API endpoints for protocol simulation and artifact generation.
"""
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import tempfile
import shutil
from typing import Optional, List
from simulator import (
    ProtocolSimulator,
    generate_deck_svg_for_robot,
    generate_well_coordinates_for_robot,
    build_deck_config,
    generate_report
)
from parameter_extractor import extract_parameters


def run_simulation_sync(protocol_path: str, metadata_dict: dict, param_values: dict = None, csv_data: dict = None) -> dict:
    """
    Run protocol simulation synchronously.
    This is called in a thread pool to avoid asyncio.run() conflicts.
    """
    simulator = ProtocolSimulator(protocol_path, metadata_dict, param_values=param_values, csv_data=csv_data)
    return simulator.simulate()

app = FastAPI(title="Opentrons Protocol Simulator API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "https://opentrons-simulator.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deploys
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary storage for simulation outputs
TEMP_DIR = Path(tempfile.gettempdir()) / "opentrons_simulator"
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "service": "Opentrons Protocol Simulator"}


@app.post("/api/extract-params")
async def extract_params(protocol_file: UploadFile = File(...)):
    """
    Extract runtime parameter definitions from a protocol without simulating.

    Args:
        protocol_file: Python protocol file (.py)

    Returns:
        JSON with has_parameters flag and parameter definitions
    """
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Protocol file must be a .py file")

    content = await protocol_file.read()
    protocol_code = content.decode('utf-8')
    result = extract_parameters(protocol_code)
    return JSONResponse(result)


@app.post("/api/simulate")
async def simulate_protocol(
    protocol_file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    param_values: Optional[str] = Form(None),
    csv_files: Optional[List[UploadFile]] = File(None),
    csv_param_mapping: Optional[str] = Form(None),
):
    """
    Simulate an Opentrons protocol and return all artifacts.

    Args:
        protocol_file: Python protocol file (.py)
        metadata: Optional JSON metadata string
        param_values: Optional JSON string of runtime parameter overrides
        csv_files: Optional CSV file uploads for CSV runtime parameters
        csv_param_mapping: Optional JSON mapping variable_name -> filename

    Returns:
        JSON with robot_config, steps, deck_layout, and SVG
    """
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Protocol file must be a .py file")

    # Parse metadata if provided
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON metadata")

    # Parse runtime parameter values if provided
    param_dict = {}
    if param_values:
        try:
            param_dict = json.loads(param_values)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in param_values")

    # Process CSV file uploads
    csv_data = {}
    if csv_files and csv_param_mapping:
        try:
            mapping = json.loads(csv_param_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in csv_param_mapping")
        for csv_file in csv_files:
            for var_name, filename in mapping.items():
                if csv_file.filename == filename:
                    content = await csv_file.read()
                    csv_data[var_name] = content.decode('utf-8')
                    break

    # Save uploaded file temporarily
    temp_protocol = TEMP_DIR / protocol_file.filename
    try:
        with temp_protocol.open('wb') as f:
            shutil.copyfileobj(protocol_file.file, f)

        # Run simulation in a thread pool to avoid asyncio.run() conflicts
        # (opentrons.simulate internally uses asyncio.run which can't be called
        # from within FastAPI's running event loop)
        result = await asyncio.to_thread(
            run_simulation_sync, str(temp_protocol), metadata_dict,
            param_dict or None, csv_data or None
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])

        # Generate deck SVG
        deck_svg = generate_deck_svg_for_robot(result['robot_config'])

        # Generate well coordinates for animation
        well_coordinates = generate_well_coordinates_for_robot(result['robot_config'])

        # Generate report
        output_dir = TEMP_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        report_md = generate_report(result['robot_config'], result['steps'], output_dir)

        # Save artifacts
        robot_json_path = output_dir / "robot.json"
        steps_json_path = output_dir / "steps.json"
        deck_svg_path = output_dir / "deck.svg"
        well_coordinates_path = output_dir / "well_coordinates.json"
        report_path = output_dir / "report.md"

        with robot_json_path.open('w') as f:
            json.dump(result['robot_config'], f, indent=2)

        with steps_json_path.open('w') as f:
            json.dump(result['steps'], f, indent=2)

        with deck_svg_path.open('w') as f:
            f.write(deck_svg)

        with well_coordinates_path.open('w') as f:
            json.dump(well_coordinates, f, indent=2)

        with report_path.open('w') as f:
            f.write(report_md)

        # Build deck config for frontend
        robot_model = result['robot_config'].get('robotModel', 'OT-2')
        deck_config = build_deck_config(robot_model)

        return JSONResponse({
            'success': True,
            'robot_config': result['robot_config'],
            'steps': result['steps'],
            'deck_layout': result['deck_layout'],
            'deck_svg': deck_svg,
            'deck_config': deck_config,
            'well_coordinates': well_coordinates,
            'report': report_md,
            'artifact_paths': {
                'robot_json': str(robot_json_path),
                'steps_json': str(steps_json_path),
                'well_coordinates': str(well_coordinates_path),
                'deck_svg': str(deck_svg_path),
                'report': str(report_path)
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp protocol file
        if temp_protocol.exists():
            temp_protocol.unlink()


@app.get("/api/download/{artifact_type}")
async def download_artifact(artifact_type: str):
    """
    Download a specific artifact.

    Args:
        artifact_type: Type of artifact (robot_json, steps_json, deck_svg, report)

    Returns:
        File download
    """
    output_dir = TEMP_DIR / "output"
    file_map = {
        'robot_json': output_dir / 'robot.json',
        'steps_json': output_dir / 'steps.json',
        'deck_svg': output_dir / 'deck.svg',
        'well_coordinates': output_dir / 'well_coordinates.json',
        'report': output_dir / 'report.md'
    }

    if artifact_type not in file_map:
        raise HTTPException(status_code=400, detail="Invalid artifact type")

    file_path = file_map[artifact_type]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=file_path.name
    )


@app.post("/api/validate")
async def validate_protocol(protocol_file: UploadFile = File(...)):
    """
    Validate a protocol without full simulation.

    Args:
        protocol_file: Python protocol file (.py)

    Returns:
        Validation results
    """
    if not protocol_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Protocol file must be a .py file")

    # Read protocol content
    content = await protocol_file.read()
    protocol_code = content.decode('utf-8')

    # Basic validation checks
    validation_results = {
        'valid': True,
        'warnings': [],
        'errors': []
    }

    # Check for API version
    if 'metadata' not in protocol_code:
        validation_results['warnings'].append("No metadata found in protocol")

    if 'apiLevel' not in protocol_code:
        validation_results['warnings'].append("API level not specified")

    # Check for run function
    if 'def run(' not in protocol_code:
        validation_results['errors'].append("No run() function found")
        validation_results['valid'] = False

    # Check for protocol_api import
    if 'protocol_api' not in protocol_code and 'ProtocolContext' not in protocol_code:
        validation_results['warnings'].append("No protocol_api import detected")

    return JSONResponse(validation_results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
