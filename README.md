# Opentrons Protocol Simulator

A full-stack web application for simulating Opentrons Python protocols without hardware. Upload a protocol file and get visual deck layouts, execution steps, and robot configuration - all in your browser.

## Features

### 🎯 Core Functionality
- **Protocol Simulation**: Execute Opentrons API v2 protocols in a simulated environment
- **Robot Configuration**: Extract pipettes, modules, and labware setup
- **Deck Visualization**: Interactive SVG visualization of 12-slot deck layout
- **Execution Steps**: Structured list of all protocol actions with filtering

### 🎨 UI Components
1. **Protocol Input Panel** - Drag & drop file upload with optional metadata
2. **Interactive Deck Visualization** - Zoomable deck layout with color-coded labware
3. **Steps Timeline** - Filterable step list with expandable details and CSV export
4. **Robot Config Inspector** - Collapsible sections for pipettes, modules, labware
5. **Validation Panel** - Protocol guidelines and example structure
6. **Export Dashboard** - Download individual or all artifacts (JSON, SVG, Markdown)

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Opentrons API** - Official Opentrons simulation library
- **Pillow & CairoSVG** - Image generation and conversion

### Frontend
- **React 18** - UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Lucide Icons** - Beautiful icon library
- **React Dropzone** - File upload handling

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd OpentronsSimulator
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Node dependencies**
```bash
npm install
```

## Running the Application

### Development Mode

1. **Start the backend server** (Terminal 1)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. **Start the frontend dev server** (Terminal 2)
```bash
npm run dev
```

3. **Open your browser**
```
http://localhost:3000
```

### Alternative: Use npm scripts

**Backend:**
```bash
npm run server
```

**Frontend:**
```bash
npm run dev
```

## Usage

1. **Upload Protocol**: Drag and drop or click to upload your `.py` protocol file
2. **Add Metadata** (Optional): Click "Show Metadata" to add custom protocol information
3. **Simulate**: Click "Simulate Protocol" to run the simulation
4. **Explore Results**:
   - View the deck layout with interactive zoom
   - Browse execution steps with filtering
   - Inspect robot configuration details
   - Download artifacts (JSON, SVG, Markdown)

## API Endpoints

### `POST /api/simulate`
Simulate a protocol and return all artifacts
- **Body**: `multipart/form-data`
  - `protocol_file`: Python protocol file (`.py`)
  - `metadata`: Optional JSON string

### `GET /api/download/{artifact_type}`
Download a specific artifact
- **Path params**: `robot_json`, `steps_json`, `deck_svg`, `report`

### `POST /api/validate`
Validate a protocol without full simulation
- **Body**: `multipart/form-data`
  - `protocol_file`: Python protocol file (`.py`)

## Project Structure

```
OpentronsSimulator/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── simulator.py         # Core simulation logic
│   └── __init__.py
├── src/
│   ├── components/
│   │   ├── ProtocolInput.jsx
│   │   ├── DeckVisualization.jsx
│   │   ├── StepsTimeline.jsx
│   │   ├── RobotConfig.jsx
│   │   ├── ValidationPanel.jsx
│   │   └── ExportDashboard.jsx
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── index.html
├── vite.config.js
├── tailwind.config.js
├── package.json
├── requirements.txt
└── README.md
```

## Output Artifacts

Each simulation generates:
- `robot.json` - Complete robot configuration
- `steps.json` - Ordered execution steps
- `deck.svg` - Deck layout visualization
- `report.md` - Summary report with stats

## Example Protocol

```python
from opentrons import protocol_api

metadata = {
    'protocolName': 'Simple Transfer',
    'author': 'Lab Tech',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Transfer
    pipette.transfer(50, plate['A1'], plate['B1'])
```

## Development

### Adding New Features
1. Backend: Add endpoints in `backend/main.py`
2. Frontend: Create components in `src/components/`
3. Update schemas in `backend/simulator.py`

### Styling
- Uses Tailwind CSS utility classes
- Custom scrollbar styles in `src/index.css`
- Color scheme: Blue (primary), Green (success), Purple (modules)

## Troubleshooting

**Issue**: CORS errors
- **Solution**: Ensure backend is running on port 8000 and frontend on port 3000

**Issue**: Import errors for Opentrons
- **Solution**: Install opentrons package: `pip install opentrons`

**Issue**: Module not found
- **Solution**: Run `npm install` to install all dependencies

## Future Enhancements

- [ ] 3D deck visualization with Three.js
- [ ] Protocol diff view for comparing versions
- [ ] Replay mode with animated step execution
- [ ] Protocol templates library
- [ ] Real-time validation with linting
- [ ] Support for Opentrons Flex robot
- [ ] Custom labware definition upload

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
