
# claude.md — Opentrons Protocol Simulator Agent

## Purpose
Turn an Opentrons Python protocol (`.py`, API v2) into three things, **without** touching real hardware:

1. **Robot configuration** — pipettes, tipracks, modules, labware defs.
2. **Deck layout** — visualized (SVG/PNG) map of all 12 positions with labware/modules.
3. **Execution steps** — a structured, human/machine-readable list of protocol actions in order.

This is a **static simulator**: it executes the protocol in a simulated context using the official `opentrons` Python API and extracts state + commands.

---

## Inputs & Outputs

### Input
- `protocol_path` (required): path to `.py` Opentrons protocol (API v2).
- `--metadata-json` (optional): extra metadata to merge.
- `--out-dir` (optional, default: `./dist`).

### Outputs
- `robot.json` — robot configuration (see schema below).
- `deck.svg` and `deck.png` — 12-slot deck visualization, with modules + labware positioned/nested.
- `steps.json` — ordered list of steps (atomic actions).
- `report.md` — short summary linking the above (optional but nice).

---

## High-Level Flow

1. **Load & simulate**  
   - Use `opentrons.simulate` (API v2) to execute the protocol in a simulator.
   - Capture:
     - Loaded labware (incl. on modules), slots, and offsets.
     - Loaded pipettes with mount, channels, tiprack compatibility.
     - Loaded modules (type, model, slot, state).
     - Command stream (with timestamps if available).

2. **Extract state**  
   - From the simulation context:
     - `context.loaded_instruments` → pipettes
     - `context.loaded_labwares` → labware + slot + namespace/loadName/version
     - `context.loaded_modules` → modules + nested labware
   - Normalize into the **Robot Config** and **Deck Layout** schemas.

3. **Normalize commands → steps**  
   - Translate low-level protocol commands into a stable step model (below).
   - Include references to pipette, source/dest well(s), volume, module targets, parameters, and any human-readable text.

4. **Render deck**  
   - Use `opentrons_shared_data.deck` and SVG assets for OT-2 (or Flex) to compose an SVG with:
     - Slots 1–12 labeled.
     - Module footprints (e.g., thermocycler spans slots 7–10).
     - Labware outlines + labels (loadName@namespace, short name if available).
   - Optionally rasterize to PNG.

5. **Write artifacts**  
   - Persist `robot.json`, `deck.svg/png`, `steps.json`, and `report.md`.

---

## Schemas

### `robot.json`
```json
{
  "robotModel": "OT-2", 
  "apiLevel": "2.x",
  "pipettes": [
    {
      "mount": "left",
      "name": "p300_single_gen2",
      "channels": 1,
      "minVolumeUl": 20,
      "maxVolumeUl": 300,
      "tiprackLoadNames": ["opentrons_96_tiprack_300ul"]
    }
  ],
  "modules": [
    {
      "slot": "1",
      "moduleType": "temperatureModuleV2",
      "model": "temperature module gen2",
      "state": { "targetTemperatureC": 4, "status": "holding" }
    }
  ],
  "labware": [
    {
      "slot": "2",
      "parent": null,
      "namespace": "opentrons",
      "loadName": "opentrons_96_tiprack_300ul",
      "version": 1,
      "label": "Tiprack 300µL"
    },
    {
      "slot": "1",
      "parent": "temperatureModuleV2:1",
      "namespace": "opentrons",
      "loadName": "biorad_96_wellplate_200ul_pcr",
      "version": 1,
      "label": "PCR Plate"
    }
  ],
  "metadata": {
    "protocolName": "…",
    "author": "…",
    "description": "…"
  }
}
```

### `steps.json`
Each item is an **atomic action** with normalized fields. Unmapped commands fall back to `"type": "other"` with raw payload.

```json
[
  {
    "idx": 1,
    "type": "aspirate",
    "pipette": "left:p300_single_gen2",
    "volumeUl": 50,
    "source": { "labware": "plate-1", "well": "A1" },
    "flowRateUlS": 50,
    "metadata": { "text": "Aspirate 50 µL from A1" }
  },
  {
    "idx": 2,
    "type": "dispense",
    "pipette": "left:p300_single_gen2",
    "volumeUl": 50,
    "dest": { "labware": "plate-1", "well": "B1" },
    "mix": null,
    "metadata": { "text": "Dispense 50 µL to B1" }
  },
  {
    "idx": 3,
    "type": "module.set_temperature",
    "module": "temperatureModuleV2:1",
    "targetC": 4,
    "metadata": { "text": "Set temp module to 4°C" }
  }
]
```

---

## User Interface Design

### Key UI Components

#### 1. **Protocol Input Panel**
- File picker for `.py` protocol files (drag-drop support)
- Optional metadata JSON upload
- Output directory selector
- "Simulate" button with progress indicator

#### 2. **Interactive Deck Visualization**
- Live 12-slot deck map (OT-2/Flex)
- Hoverable labware/modules showing details (loadName, slot, capacity)
- Color-coding: modules (blue), labware (gray), tipracks (green)
- Toggle between SVG and PNG export preview
- Zoom/pan controls for detail inspection

#### 3. **Steps Timeline/List**
- Scrollable step-by-step execution view
- Step type icons (aspirate ↓, dispense ↑, temp 🌡️, mix 🔄)
- Filtering by: pipette, labware, action type
- Click step → highlight affected wells/labware on deck
- Export to CSV/Excel option

#### 4. **Robot Config Inspector**
- Collapsible sections: Pipettes, Modules, Labware
- Pipette card: mount, volume range, compatible tipracks
- Module card: type, slot, current state (temp/speed)
- Labware tree view showing nesting (e.g., plate on module)

#### 5. **Validation & Errors Panel**
- Pre-simulation checks (API version, missing labware defs)
- Runtime warnings (volume out of range, missing tips)
- Error highlighting with line numbers in protocol

#### 6. **Export Dashboard**
- Quick download buttons for all artifacts
- Preview `report.md` in-app (markdown renderer)
- Share/copy shareable link to outputs

### Tech Stack Suggestions
- **Web**: React + D3.js (deck SVG manipulation) or Three.js (3D deck)
- **Desktop**: Electron wrapper for offline use
- **Backend**: Flask/FastAPI serving simulation API

### UX Enhancements
- **Diff view** for comparing two protocols side-by-side
- **Replay mode** animating steps on deck with playback controls
- **Templates library** for common protocol patterns
- **Protocol validation** before simulation (lint-style checks)

---

## Implementation Status

### ✅ Completed Features

#### Backend (Python/FastAPI)
- [x] Core simulation engine (`simulator.py`)
- [x] Protocol parsing and execution
- [x] Robot configuration extraction
- [x] Steps normalization
- [x] Deck layout generation
- [x] SVG rendering
- [x] REST API endpoints (`/api/simulate`, `/api/download`, `/api/validate`)
- [x] CORS middleware for frontend integration
- [x] File upload handling
- [x] Artifact generation (JSON, SVG, Markdown)

#### Frontend (React/Vite)
- [x] Protocol Input Panel with drag-drop
- [x] Interactive Deck Visualization with zoom
- [x] Steps Timeline with filtering and CSV export
- [x] Robot Config Inspector with collapsible sections
- [x] Validation Panel with guidelines
- [x] Export Dashboard with download options
- [x] Responsive layout with Tailwind CSS
- [x] Error handling and loading states

#### Developer Experience
- [x] Setup scripts (Windows/Unix)
- [x] Documentation (README, QUICKSTART)
- [x] Sample protocol
- [x] Project structure
- [x] npm scripts for dev/build/clean

### Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (React/Vite)             │
│  ┌───────────────────────────────────────┐  │
│  │  Protocol Input Panel                 │  │
│  │  - File upload (drag & drop)          │  │
│  │  - Metadata JSON input                │  │
│  └───────────────────────────────────────┘  │
│                     ↓                        │
│  ┌───────────────────────────────────────┐  │
│  │  Visualization Layer                  │  │
│  │  - Deck Layout (SVG + Zoom)           │  │
│  │  - Steps Timeline (Filter + Export)   │  │
│  │  - Config Inspector (Collapsible)     │  │
│  └───────────────────────────────────────┘  │
│                     ↓                        │
│  ┌───────────────────────────────────────┐  │
│  │  Export Dashboard                     │  │
│  │  - JSON/SVG/MD downloads              │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                      ↕ HTTP/REST API
┌─────────────────────────────────────────────┐
│         Backend (Python/FastAPI)            │
│  ┌───────────────────────────────────────┐  │
│  │  API Endpoints                        │  │
│  │  POST /api/simulate                   │  │
│  │  GET  /api/download/{type}            │  │
│  │  POST /api/validate                   │  │
│  └───────────────────────────────────────┘  │
│                     ↓                        │
│  ┌───────────────────────────────────────┐  │
│  │  ProtocolSimulator                    │  │
│  │  - Load & execute protocol            │  │
│  │  - Extract pipettes/modules/labware   │  │
│  │  - Normalize commands → steps         │  │
│  │  - Generate deck visualization        │  │
│  └───────────────────────────────────────┘  │
│                     ↓                        │
│  ┌───────────────────────────────────────┐  │
│  │  Opentrons Simulation API             │  │
│  │  - opentrons.simulate                 │  │
│  │  - ProtocolContext                    │  │
│  │  - Hardware abstraction               │  │
│  └───────────────────────────────────────┘  │
│                     ↓                        │
│  ┌───────────────────────────────────────┐  │
│  │  Output Generation                    │  │
│  │  - robot.json (config)                │  │
│  │  - steps.json (execution)             │  │
│  │  - deck.svg (visual)                  │  │
│  │  - report.md (summary)                │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Data Flow

```
Protocol.py Upload
       ↓
API: POST /api/simulate
       ↓
ProtocolSimulator.simulate()
       ↓
opentrons.simulate()
       ↓
Extract State:
  - context.loaded_instruments → pipettes
  - context.loaded_labwares → labware
  - context.loaded_modules → modules
  - runlog → steps
       ↓
Generate Artifacts:
  - robot.json
  - steps.json
  - deck.svg
  - report.md
       ↓
Return to Frontend
       ↓
Render UI Components:
  - DeckVisualization (SVG)
  - StepsTimeline (interactive list)
  - RobotConfig (collapsible)
  - ExportDashboard (downloads)
```
