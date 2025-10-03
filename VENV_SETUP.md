# Virtual Environment Setup

The project uses a Python virtual environment named **`otsimenv`** to isolate dependencies.

## Quick Start

The virtual environment has already been created and dependencies installed!

### Running the Application

**Backend:**
```bash
npm run server
```
This automatically uses the virtual environment's Python.

**Frontend:**
```bash
npm run dev
```

## Manual Virtual Environment Commands

### Activate Virtual Environment

**Windows:**
```cmd
otsimenv\Scripts\activate
```

**Unix/macOS:**
```bash
source otsimenv/bin/activate
```

### Deactivate
```bash
deactivate
```

### Install Dependencies Manually
```bash
# Windows
otsimenv\Scripts\pip.exe install -r requirements.txt

# Unix/macOS
otsimenv/bin/pip install -r requirements.txt
```

### Reinstall Virtual Environment
```bash
# Remove old venv
rm -rf otsimenv  # or rmdir /s otsimenv on Windows

# Create new
python -m venv otsimenv

# Install dependencies
otsimenv\Scripts\pip.exe install -r requirements.txt  # Windows
# or
otsimenv/bin/pip install -r requirements.txt  # Unix/macOS
```

## Why Virtual Environment?

1. **Dependency Isolation**: Prevents conflicts with system Python packages
2. **Version Control**: Ensures everyone uses the same package versions
3. **Clean Setup**: Easy to reset by deleting and recreating
4. **No System Pollution**: Doesn't affect global Python installation

## Troubleshooting

### "Module not found" errors
Make sure you're using the venv Python:
```bash
npm run server  # Uses venv automatically
```

### Activate script not found
The venv might not be created. Run:
```bash
python -m venv otsimenv
otsimenv\Scripts\pip.exe install -r requirements.txt
```

### Permission errors
On Unix/macOS, you might need to make scripts executable:
```bash
chmod +x otsimenv/bin/activate
```

## Notes

- The `otsimenv/` directory is in `.gitignore` (not committed to Git)
- Each developer creates their own local virtual environment
- The setup.bat/setup.sh scripts handle venv creation automatically
