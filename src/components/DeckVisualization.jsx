import { useState, useEffect } from 'react'
import { ZoomIn, ZoomOut, Maximize2, Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react'

export default function DeckVisualization({
  deckSvg,
  deckLayout,
  steps = [],
  wellCoordinates = {},
  pipettes = [],
  currentStepIndex,
  onStepChange
}) {
  const [zoom, setZoom] = useState(1)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5))
  const handleReset = () => setZoom(1)

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !steps.length) return

    const stepDuration = 1600 // ms
    const timer = setTimeout(() => {
      if (currentStepIndex < steps.length - 1) {
        onStepChange?.(currentStepIndex + 1)
      } else {
        setIsPlaying(false) // End of protocol
      }
    }, stepDuration)

    return () => clearTimeout(timer)
  }, [isPlaying, currentStepIndex, steps.length, onStepChange])

  // Playback control handlers
  const handlePlayPause = () => {
    if (currentStepIndex === -1 || currentStepIndex >= steps.length - 1) {
      onStepChange?.(0) // Start from beginning
    }
    setIsPlaying(!isPlaying)
  }

  const handleStepForward = () => {
    onStepChange?.(Math.min(currentStepIndex + 1, steps.length - 1))
    setIsPlaying(false)
  }

  const handleStepBackward = () => {
    onStepChange?.(Math.max(currentStepIndex - 1, 0))
    setIsPlaying(false)
  }

  const handleResetAnimation = () => {
    onStepChange?.(-1)
    setIsPlaying(false)
  }

  // Get well coordinates from mapping
  const getWellCoordinates = (labwareLabel, wellId) => {
    for (const slot in wellCoordinates) {
      if (wellCoordinates[slot][labwareLabel]?.[wellId]) {
        return wellCoordinates[slot][labwareLabel][wellId]
      }
    }
    return null
  }

  const getLabwareInfo = (labwareLabel) => {
    for (const slot in wellCoordinates) {
      const labwareMap = wellCoordinates[slot][labwareLabel]
      if (labwareMap) {
        const wellIds = Object.keys(labwareMap)
        const rowSet = new Set()
        let maxCol = 0

        for (const wellId of wellIds) {
          const match = wellId.match(/^([A-Z]+)(\d+)$/)
          if (!match) continue
          const row = match[1]
          const col = parseInt(match[2], 10)
          rowSet.add(row)
          if (col > maxCol) maxCol = col
        }

        const rowLetters = Array.from(rowSet).sort((a, b) => a.localeCompare(b))
        return {
          wellMap: labwareMap,
          rowLetters,
          rows: rowLetters.length,
          cols: maxCol
        }
      }
    }
    return null
  }

  const getPipetteChannels = (step) => {
    if (!step?.pipette) return 1
    const parts = step.pipette.split(':')
    const pipetteName = parts.length > 1 ? parts[1] : step.pipette
    const match = pipettes.find(p => p.name === pipetteName)
    if (match?.channels) return match.channels
    if (pipetteName.toLowerCase().includes('multi')) return 8
    return 1
  }

  const expandWellTargets = (labwareLabel, wellId, isMulti) => {
    const info = getLabwareInfo(labwareLabel)
    if (!info) return [wellId]

    const isReservoir = labwareLabel.toLowerCase().includes('reservoir')
    if (isReservoir) {
      return Object.keys(info.wellMap)
    }

    if (!isMulti) return [wellId]

    const match = wellId.match(/^([A-Z]+)(\d+)$/)
    if (!match) return [wellId]

    const targetRow = match[1]
    const targetCol = match[2]

    if (info.rows === 16 && info.cols === 24) {
      const rowIndex = info.rowLetters.indexOf(targetRow)
      const parity = rowIndex >= 0 ? rowIndex % 2 : 0
      return info.rowLetters
        .filter((_, idx) => idx % 2 === parity)
        .map(row => `${row}${targetCol}`)
        .filter(id => info.wellMap[id])
    }

    return info.rowLetters
      .map(row => `${row}${targetCol}`)
      .filter(id => info.wellMap[id])
  }

  // Render triangle indicator
  const renderTriangle = (type, x, y, key) => {
    const configs = {
      aspirate: { color: '#10b981', direction: 'up' },
      dispense: { color: '#ef4444', direction: 'down' },
      distribute: { color: '#10b981', direction: 'up' },
      transfer: { color: '#10b981', direction: 'up' },
      pick_up_tip: { color: '#000000', direction: 'up' },
      drop_tip: { color: '#000000', direction: 'down' }
    }

    const config = configs[type] || configs.aspirate
    const { color, direction } = config

    const points = direction === 'up'
      ? `${x},${y+8} ${x+6},${y} ${x+12},${y+8}`
      : `${x},${y} ${x+6},${y+8} ${x+12},${y}`

    return (
      <polygon
        key={key}
        points={points}
        fill={color}
        opacity="0.8"
        style={{ transition: 'opacity 0.4s' }}
      />
    )
  }

  // Render animation indicators for current step
  const renderAnimationIndicators = () => {
    if (currentStepIndex < 0 || currentStepIndex >= steps.length) {
      return null
    }

    const step = steps[currentStepIndex]
    const indicators = []
    const channels = getPipetteChannels(step)
    const isMulti = channels >= 8

    console.log('Current step:', step)
    console.log('Well coordinates:', wellCoordinates)

    // Handle source well (aspirate, pick_up_tip)
    if (step.source?.labware && step.source?.well) {
      const wells = expandWellTargets(step.source.labware, step.source.well, isMulti)
      for (const wellId of wells) {
        const coords = getWellCoordinates(step.source.labware, wellId)
        console.log(`Looking for source: ${step.source.labware} - ${wellId}, found:`, coords)
        if (coords) {
          indicators.push(renderTriangle(step.type, coords.x - 6, coords.y - 8, `source-${step.idx}-${wellId}`))
        }
      }
    }

    // Handle destination well (dispense, drop_tip)
    if (step.dest?.labware && step.dest?.well) {
      const wells = expandWellTargets(step.dest.labware, step.dest.well, isMulti)
      for (const wellId of wells) {
        const coords = getWellCoordinates(step.dest.labware, wellId)
        console.log(`Looking for dest: ${step.dest.labware} - ${wellId}, found:`, coords)
        if (coords) {
          const destType = step.type.includes('drop') ? 'drop_tip' : 'dispense'
          indicators.push(renderTriangle(destType, coords.x - 6, coords.y - 8, `dest-${step.idx}-${wellId}`))
        }
      }
    }

    // Handle module operations (pulse slot border)
    if (step.type && step.type.startsWith('module.')) {
      // Extract module info from step
      const moduleName = step.module
      if (moduleName) {
        // Find module slot from wellCoordinates keys or module name
        // For now, check if any slot has module-related labware
        for (const slot in wellCoordinates) {
          const slotLabware = Object.keys(wellCoordinates[slot])
          // If module command references a slot or labware
          if (moduleName.includes(slot) || slotLabware.some(lw => moduleName.includes(lw))) {
            indicators.push(renderModulePulse(parseInt(slot), `module-${step.idx}`))
            break
          }
        }
      }
    }

    return indicators
  }

  // Render module pulse animation
  const renderModulePulse = (slotNumber, key) => {
    // Calculate slot position (same logic as generate_deck_svg)
    const slot_width = 200
    const slot_height = 120
    const margin = 50

    const slot_index = slotNumber - 1
    const row = 3 - Math.floor(slot_index / 3) // Flip vertically
    const col = slot_index % 3
    const slot_x = margin + col * slot_width
    const slot_y = margin + row * slot_height

    return (
      <rect
        key={key}
        x={slot_x}
        y={slot_y}
        width={190}
        height={110}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="3"
        opacity="0.6"
        className="animate-pulse"
      />
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Deck Layout</h2>
        <div className="flex gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title="Reset Zoom"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Playback Controls */}
      {steps.length > 0 && (
        <div className="flex items-center gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
          <button
            onClick={handlePlayPause}
            className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>

          <button
            onClick={handleStepBackward}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Step Backward"
            disabled={currentStepIndex <= 0}
          >
            <SkipBack size={20} />
          </button>

          <button
            onClick={handleStepForward}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Step Forward"
            disabled={currentStepIndex >= steps.length - 1}
          >
            <SkipForward size={20} />
          </button>

          <button
            onClick={handleResetAnimation}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
            title="Reset"
          >
            <RotateCcw size={20} />
          </button>

          <div className="text-sm text-gray-600 ml-auto">
            {currentStepIndex >= 0
              ? `Step ${currentStepIndex + 1} / ${steps.length}`
              : `${steps.length} steps`
            }
          </div>
        </div>
      )}

      {/* SVG Display */}
      <div className="border border-gray-200 rounded-lg overflow-auto bg-gray-50 p-4">
        <div
          className="transition-transform origin-top-left relative"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Static deck SVG */}
          <div dangerouslySetInnerHTML={{ __html: deckSvg }} />

          {/* Animation overlay layer */}
          <svg
            width="800"
            height="600"
            xmlns="http://www.w3.org/2000/svg"
            style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
          >
            <g id="animation-layer">
              {renderAnimationIndicators()}
            </g>
          </svg>
        </div>
      </div>

      {/* Deck Info */}
      {deckLayout && (
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div className="bg-blue-50 p-3 rounded">
            <span className="text-gray-600">Total Slots:</span>
            <span className="ml-2 font-semibold">{deckLayout.slots?.length || 12}</span>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <span className="text-gray-600">Occupied:</span>
            <span className="ml-2 font-semibold">{deckLayout.occupied?.length || 0}</span>
          </div>
        </div>
      )}

      {/* Color Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded"></div>
          <span>Modules</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 border-2 border-green-500 rounded"></div>
          <span>Tipracks</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-100 border-2 border-gray-500 rounded"></div>
          <span>Labware</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-100 border-2 border-red-500 rounded"></div>
          <span>Trash</span>
        </div>
      </div>
    </div>
  )
}
