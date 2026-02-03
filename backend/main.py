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
from typing import Optional
from simulator import ProtocolSimulator, generate_deck_svg, generate_report


def run_simulation_sync(protocol_path: str, metadata_dict: dict) -> dict:
    """
    Run protocol simulation synchronously.
    This is called in a thread pool to avoid asyncio.run() conflicts.
    """
    simulator = ProtocolSimulator(protocol_path, metadata_dict)
    return simulator.simulate()

app = FastAPI(title="Opentrons Protocol Simulator API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


@app.post("/api/simulate")
async def simulate_protocol(
    protocol_file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Simulate an Opentrons protocol and return all artifacts.

    Args:
        protocol_file: Python protocol file (.py)
        metadata: Optional JSON metadata string

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

    # Save uploaded file temporarily
    temp_protocol = TEMP_DIR / protocol_file.filename
    try:
        with temp_protocol.open('wb') as f:
            shutil.copyfileobj(protocol_file.file, f)

        # Run simulation in a thread pool to avoid asyncio.run() conflicts
        # (opentrons.simulate internally uses asyncio.run which can't be called
        # from within FastAPI's running event loop)
        result = await asyncio.to_thread(
            run_simulation_sync, str(temp_protocol), metadata_dict
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])

        # Generate deck SVG
        deck_svg = generate_deck_svg(result['robot_config'])

        # Generate report
        output_dir = TEMP_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        report_md = generate_report(result['robot_config'], result['steps'], output_dir)

        # Save artifacts
        robot_json_path = output_dir / "robot.json"
        steps_json_path = output_dir / "steps.json"
        deck_svg_path = output_dir / "deck.svg"
        report_path = output_dir / "report.md"

        with robot_json_path.open('w') as f:
            json.dump(result['robot_config'], f, indent=2)

        with steps_json_path.open('w') as f:
            json.dump(result['steps'], f, indent=2)

        with deck_svg_path.open('w') as f:
            f.write(deck_svg)

        with report_path.open('w') as f:
            f.write(report_md)

        return JSONResponse({
            'success': True,
            'robot_config': result['robot_config'],
            'steps': result['steps'],
            'deck_layout': result['deck_layout'],
            'deck_svg': deck_svg,
            'report': report_md,
            'artifact_paths': {
                'robot_json': str(robot_json_path),
                'steps_json': str(steps_json_path),
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
