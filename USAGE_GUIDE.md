# 📘 Opentrons Protocol Simulator - Usage Guide

A step-by-step guide to using the Opentrons Protocol Simulator.

## 🚀 Getting Started

### Step 1: Start the Application

#### Option A: Quick Start (Recommended)
```bash
# Windows
setup.bat

# macOS/Linux
chmod +x setup.sh && ./setup.sh
```

Then run:
```bash
# Terminal 1: Backend
npm run server

# Terminal 2: Frontend
npm run dev
```

#### Option B: Manual Start
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend (from root)
npm run dev
```

### Step 2: Open the Application
Navigate to **http://localhost:3000** in your browser.

---

## 📝 Using the Simulator

### 1️⃣ Upload Your Protocol

#### Method 1: Drag and Drop
1. Locate the **Protocol Input** panel at the top
2. Drag your `.py` protocol file onto the upload area
3. The file will be highlighted in green when accepted

#### Method 2: Click to Browse
1. Click anywhere in the upload area
2. Select your `.py` protocol file from the file dialog
3. Click "Open"

**Accepted Files:** Only `.py` (Python) files are accepted

#### Optional: Add Metadata
1. Click **"Show Metadata"** button
2. Enter JSON metadata:
   ```json
   {
     "protocolName": "PCR Setup",
     "author": "Lab Technician",
     "description": "Automated PCR plate preparation"
   }
   ```
3. This will be merged with the protocol's metadata

### 2️⃣ Run the Simulation

1. Click the **"Simulate Protocol"** button
2. Wait for the simulation to complete (usually 2-5 seconds)
3. Results will appear below

**During Simulation:**
- Button shows "Simulating..." with a spinner
- Backend processes the protocol
- Opentrons API executes in virtual environment

**After Simulation:**
- Success: Results display automatically
- Error: Red error banner shows the issue

---

## 🔍 Exploring Results

### 🗺️ Deck Visualization

**What it shows:** Visual representation of your 12-slot OT-2 deck

**Features:**
- **Zoom Controls:**
  - 🔍 Zoom In: Enlarge the deck view
  - 🔍 Zoom Out: Shrink the deck view
  - ⊡ Reset: Return to original size

- **Color Coding:**
  - 🔵 Blue border: Modules
  - ⬜ Gray border: Labware
  - 🟢 Green border: Tipracks

- **Slot Information:**
  - Each slot shows its number (1-12)
  - Occupied slots display labware names
  - Empty slots appear blank

**Tips:**
- Zoom in to see labware details clearly
- Check for correct slot assignments
- Verify module placement (e.g., thermocycler spans slots 7-10)

### 📋 Steps Timeline

**What it shows:** Every action your protocol performs, in order

**Features:**

#### Step Icons
- ↓ **Aspirate** - Drawing liquid
- ↑ **Dispense** - Dispensing liquid
- 🔧 **Pick Up Tip** - Getting a new tip
- 🗑️ **Drop Tip** - Disposing tip
- 🔄 **Mix** - Mixing liquids
- 🌡️ **Temperature** - Module temperature change
- • **Other** - Other commands

#### Filtering
1. Click the dropdown menu
2. Select a step type to filter
3. View only steps of that type
4. Select "All Steps" to reset

#### Expanding Details
1. Click the ⌄ icon on any step
2. See detailed information:
   - Pipette used
   - Volume transferred
   - Source well (labware + well ID)
   - Destination well
   - Flow rate
   - Temperature (for module commands)

#### Export to CSV
1. Click the **"CSV"** button
2. File downloads automatically as `protocol_steps.csv`
3. Open in Excel, Google Sheets, etc.

**CSV Format:**
```csv
Step,Type,Description
1,aspirate,"Aspirate 50 µL from A1"
2,dispense,"Dispense 50 µL to B1"
```

### ⚙️ Robot Config Inspector

**What it shows:** Complete hardware configuration

**Sections:**

#### 1. Pipettes
- Mount position (left/right)
- Pipette model name
- Number of channels (1 or 8)
- Volume range (min-max µL)
- Compatible tipracks

**Example:**
```
p300_single_gen2
Mount: left
Channels: 1
Volume Range: 20 - 300 µL
Compatible Tipracks: opentrons_96_tiprack_300ul
```

#### 2. Modules
- Module type (temperature, magnetic, thermocycler)
- Slot location
- Model/generation
- Current state (temperature, speed, status)

**Example:**
```
temperatureModuleV2
Slot: 1
Model: temperature module gen2
State:
  Temperature: 4°C
  Status: holding
```

#### 3. Labware
- Labware name/label
- Slot position
- Load name (official identifier)
- Parent module (if on a module)

**Example:**
```
PCR Plate
Slot: 1
Load Name: biorad_96_wellplate_200ul_pcr
Parent: temperatureModuleV2:1
```

**Interaction:**
- Click section headers to expand/collapse
- Pipettes section expanded by default
- All sections independently collapsible

### 📥 Export Dashboard

**What it shows:** Download options for all generated files

**Available Downloads:**

#### 1. Robot Config (robot.json)
- Complete configuration in JSON format
- Includes pipettes, modules, labware
- Machine-readable for further processing

#### 2. Execution Steps (steps.json)
- All protocol steps in structured format
- Ordered by execution sequence
- Includes parameters for each step

#### 3. Deck Layout (deck.svg)
- Visual deck image in SVG format
- Scalable vector graphics
- Can be edited in Illustrator, Inkscape, etc.

#### 4. Summary Report (report.md)
- Markdown summary document
- Protocol statistics
- Links to other artifacts
- Human-readable overview

**Download Methods:**

1. **Individual Download:**
   - Click the download icon on any artifact
   - File downloads immediately

2. **Download All:**
   - Click **"Download All Artifacts"** button
   - All 4 files download sequentially

3. **Preview Report:**
   - Click **"Show Report Preview"**
   - Read the markdown report in-app
   - Click again to hide

---

## ✅ Validation & Best Practices

### Before Simulating

The **Validation Panel** (shown when no results) provides:

1. **Protocol Structure Requirements:**
   - Must have a `run()` function
   - Function accepts `ProtocolContext` parameter
   - Include metadata dictionary

2. **API Level:**
   - Specify in metadata: `"apiLevel": "2.14"`
   - Use compatible Opentrons API version

3. **Import Statement:**
   - Use: `from opentrons import protocol_api`

4. **Example Protocol:**
   - Complete working example provided
   - Copy and modify as needed

### Common Issues

#### ❌ No run() function found
**Solution:** Add this structure to your protocol:
```python
def run(protocol: protocol_api.ProtocolContext):
    # Your code here
    pass
```

#### ❌ API level not specified
**Solution:** Add metadata at the top:
```python
metadata = {
    'apiLevel': '2.14'
}
```

#### ❌ Invalid labware name
**Solution:** Use official Opentrons labware names from their library

#### ❌ File upload failed
**Solution:** Ensure file is `.py` format and under 10MB

---

## 🎯 Workflow Examples

### Example 1: Quick Protocol Check

1. Upload your protocol
2. Click "Simulate"
3. Check deck layout for correctness
4. Review steps count
5. Download `report.md` for records

**Time:** ~1 minute

### Example 2: Detailed Analysis

1. Upload protocol
2. Simulate
3. **Deck:** Verify all labware in correct slots
4. **Steps:** Filter by "aspirate" to check volumes
5. **Config:** Expand pipettes, verify tipracks
6. **Export:** Download all artifacts
7. **CSV:** Export steps for spreadsheet analysis

**Time:** ~5 minutes

### Example 3: Protocol Development

1. Write protocol in your IDE
2. Upload to simulator
3. Check for errors
4. Review deck layout
5. Iterate on protocol
6. Re-upload and re-simulate
7. Export final artifacts

**Time:** Iterative

---

## 🔧 Advanced Features

### Custom Metadata

Add rich metadata for better reports:
```json
{
  "protocolName": "High-Throughput Screening",
  "author": "Dr. Jane Smith",
  "description": "96-well compound screening assay",
  "created": "2025-10-03",
  "apiLevel": "2.14",
  "source": "Lab Protocol #12345"
}
```

### Analyzing Complex Protocols

For protocols with 100+ steps:
1. Use step filtering extensively
2. Export CSV for Excel pivot tables
3. Look for patterns in step summary
4. Check for unexpected step types

### Deck Layout Verification

1. Zoom in to check overlaps
2. Verify module compatibility
3. Check tiptrack accessibility
4. Ensure labware fits in slots

---

## 🐛 Troubleshooting

### Simulation Fails

**Check:**
- Protocol syntax is valid Python
- All imports are correct
- Labware names are official Opentrons names
- API level matches your protocol

**Error Messages:**
- Read the error carefully
- Check line numbers (if provided)
- Validate protocol structure

### UI Not Loading

**Check:**
- Backend is running on port 8000
- Frontend is running on port 3000
- No CORS errors in browser console
- Try clearing browser cache

### Downloads Not Working

**Check:**
- Simulation completed successfully
- Artifacts were generated (check backend logs)
- Browser allows downloads
- Popup blocker isn't active

---

## 💡 Tips & Tricks

1. **Use the Sample Protocol**
   - Start with `examples/sample_protocol.py`
   - Modify incrementally
   - Test each change

2. **Version Control**
   - Keep protocol files in Git
   - Download artifacts for each version
   - Compare changes over time

3. **Batch Analysis**
   - Simulate multiple protocols
   - Compare deck layouts
   - Analyze step patterns

4. **Documentation**
   - Download reports for each protocol
   - Include in lab notebooks
   - Share with team members

5. **Development Workflow**
   - Write protocol
   - Simulate locally
   - Fix issues
   - Run on real hardware

---

## 📞 Getting Help

### Resources
- **README.md** - Full documentation
- **QUICKSTART.md** - Setup guide
- **CONTRIBUTING.md** - Development guide
- **Examples/** - Sample protocols

### Support
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Documentation: Search docs first

---

## 🎓 Next Steps

1. ✅ Try the sample protocol
2. ✅ Upload your own protocol
3. ✅ Explore all UI features
4. ✅ Download artifacts
5. ✅ Integrate into your workflow

**Happy Simulating!** 🔬✨
