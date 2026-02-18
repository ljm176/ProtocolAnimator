# Contributing to Protocol Animator

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/ProtocolAnimator.git
   cd ProtocolAnimator
   ```

2. **Install Dependencies**
   ```bash
   # Quick setup
   ./setup.sh        # Unix/macOS
   setup.bat         # Windows

   # Or manual
   pip install -r requirements.txt
   npm install
   ```

3. **Run Development Servers**
   ```bash
   # Terminal 1 - Backend
   npm run server

   # Terminal 2 - Frontend
   npm run dev
   ```

## Project Structure

```
ProtocolAnimator/
├── backend/              # Python FastAPI backend
│   ├── main.py          # API endpoints
│   ├── simulator.py     # Core simulation logic
│   └── __init__.py
├── src/                 # React frontend
│   ├── components/      # UI components
│   │   ├── ProtocolInput.jsx
│   │   ├── DeckVisualization.jsx
│   │   ├── StepsTimeline.jsx
│   │   ├── RobotConfig.jsx
│   │   ├── ValidationPanel.jsx
│   │   └── ExportDashboard.jsx
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── examples/           # Sample protocols
└── docs/              # Documentation
```

## How to Contribute

### 🐛 Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/ProtocolAnimator/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, Python version, Node version)

### ✨ Suggesting Features

1. Check [existing feature requests](https://github.com/yourusername/ProtocolAnimator/issues?q=label%3Aenhancement)
2. Create a new issue with:
   - Clear use case
   - Expected behavior
   - Why this would be useful
   - Possible implementation approach

### 🔧 Pull Requests

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make Your Changes**
   - Follow the coding standards below
   - Add tests if applicable
   - Update documentation

3. **Test Your Changes**
   ```bash
   # Test backend
   cd backend
   python -m pytest  # if tests exist

   # Test frontend
   npm run build
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new deck visualization feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `style:` Formatting
   - `refactor:` Code restructuring
   - `test:` Adding tests
   - `chore:` Maintenance

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Coding Standards

### Python (Backend)

- **Style**: Follow PEP 8
- **Docstrings**: Use Google style
- **Type Hints**: Use when possible

```python
def simulate_protocol(protocol_path: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Simulate a protocol.

    Args:
        protocol_path: Path to the protocol file
        metadata: Optional metadata dictionary

    Returns:
        Dictionary containing simulation results
    """
    pass
```

### JavaScript/React (Frontend)

- **Style**: Use ESLint (if configured)
- **Components**: Functional components with hooks
- **Props**: Use PropTypes or TypeScript
- **Naming**: PascalCase for components, camelCase for functions/variables

```jsx
export default function MyComponent({ config, onUpdate }) {
  const [state, setState] = useState(null)

  const handleClick = () => {
    // handler logic
  }

  return (
    <div className="container">
      {/* JSX */}
    </div>
  )
}
```

### CSS (Tailwind)

- Use Tailwind utility classes
- Custom styles in `index.css` if necessary
- Responsive: mobile-first approach

```jsx
<div className="p-4 bg-white rounded-lg shadow-md md:p-6 lg:p-8">
  {/* Content */}
</div>
```

## Adding New Features

### Backend: New API Endpoint

1. **Add endpoint in `backend/main.py`**
   ```python
   @app.post("/api/new-feature")
   async def new_feature(data: YourModel):
       # Implementation
       return {"result": "success"}
   ```

2. **Update simulator if needed** (`backend/simulator.py`)

3. **Test the endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/new-feature
   ```

### Frontend: New Component

1. **Create component** in `src/components/`
   ```jsx
   // src/components/NewFeature.jsx
   export default function NewFeature({ prop1, prop2 }) {
     return (
       <div className="bg-white p-4 rounded-lg">
         {/* Component content */}
       </div>
     )
   }
   ```

2. **Import in `App.jsx`**
   ```jsx
   import NewFeature from './components/NewFeature'

   function App() {
     return (
       <div>
         <NewFeature prop1={data} prop2={handler} />
       </div>
     )
   }
   ```

3. **Style with Tailwind** in the component

## Testing

### Backend Tests (Future)
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests (Future)
```bash
npm test
```

### Manual Testing Checklist
- [ ] Upload a valid protocol
- [ ] Upload an invalid protocol
- [ ] Test all download buttons
- [ ] Test step filtering
- [ ] Test deck zoom controls
- [ ] Test responsive layout (mobile/tablet/desktop)
- [ ] Test error states

## Documentation

When adding features, update:
1. **README.md** - User-facing documentation
2. **QUICKSTART.md** - Getting started guide
3. **claude.md** - Technical specification
4. **Code comments** - Inline documentation
5. **API docs** - If adding endpoints

## Performance

- **Backend**: Minimize simulation time
- **Frontend**: Optimize re-renders with `useMemo`, `useCallback`
- **Bundle**: Keep bundle size small (check with `npm run build`)

## Accessibility

- Use semantic HTML
- Add ARIA labels where needed
- Ensure keyboard navigation works
- Test with screen readers when possible

## Release Process

1. Update version in `package.json`
2. Update CHANGELOG.md
3. Create release notes
4. Tag release: `git tag v1.x.x`
5. Push: `git push --tags`

## Need Help?

- **Questions**: Open a [Discussion](https://github.com/yourusername/ProtocolAnimator/discussions)
- **Bugs**: Open an [Issue](https://github.com/yourusername/ProtocolAnimator/issues)
- **Chat**: Join our community (if available)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project and community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Protocol Animator! 🔬✨
