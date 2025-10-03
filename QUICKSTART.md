# Quick Start Guide

Get up and running with Opentrons Protocol Simulator in 5 minutes!

## 🚀 Quick Setup

### Windows
```bash
setup.bat
```

### macOS/Linux
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run servers
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
npm run dev
```

## 📝 Try the Sample Protocol

1. Start both servers (backend + frontend)
2. Open http://localhost:3000
3. Upload the sample protocol from `examples/sample_protocol.py`
4. Click "Simulate Protocol"
5. Explore the results!

## 🎯 What You'll See

### 1. Deck Visualization
- 12-slot deck layout
- Color-coded labware and modules
- Interactive zoom controls

### 2. Execution Steps
- Filterable step timeline
- Expandable step details
- Export to CSV

### 3. Robot Configuration
- Pipettes with specs
- Module states
- Labware tree view

### 4. Export Options
- `robot.json` - Full robot config
- `steps.json` - All protocol steps
- `deck.svg` - Visual deck layout
- `report.md` - Summary report

## 🔧 Troubleshooting

**Backend not starting?**
- Make sure port 8000 is free
- Check Python version: `python --version` (need 3.8+)
- Verify opentrons installed: `pip show opentrons`

**Frontend not loading?**
- Make sure port 3000 is free
- Check Node version: `node --version` (need 16+)
- Clear npm cache: `npm cache clean --force`

**CORS errors?**
- Ensure backend runs on port 8000
- Ensure frontend runs on port 3000
- Restart both servers

## 📚 Next Steps

1. **Create Your Own Protocol**
   - Use the example in `examples/sample_protocol.py` as a template
   - Follow Opentrons API v2 documentation
   - Test with the simulator

2. **Customize the UI**
   - Edit components in `src/components/`
   - Modify styles in Tailwind classes
   - Add new visualization features

3. **Extend the Backend**
   - Add new endpoints in `backend/main.py`
   - Enhance simulation in `backend/simulator.py`
   - Add validation rules

## 💡 Tips

- **Upload Speed**: Smaller protocol files load faster
- **Metadata**: Add JSON metadata for richer reports
- **Validation**: Check protocol structure before simulation
- **Export All**: Download all artifacts at once for complete records

## 🐛 Common Issues

### Import Error: No module named 'opentrons'
```bash
pip install opentrons
```

### Module not found: react-dropzone
```bash
npm install
```

### Port already in use
```bash
# Backend (8000)
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows

# Frontend (3000)
lsof -ti:3000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :3000   # Windows
```

## 🎓 Learn More

- [Opentrons API Docs](https://docs.opentrons.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)

---

**Need help?** Open an issue on GitHub or check the full README.md
