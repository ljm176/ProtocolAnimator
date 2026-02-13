import { useState, useEffect } from 'react'
import { ZoomIn, ZoomOut, Maximize2, Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react'

export default function DeckVisualization({
  deckSvg,
  deckLayout,
  deckConfig,
  robotModel,
  steps = [],
  wellCoordinates = {},
  pipettes = [],
  currentStepIndex,
  onStepChange
}) {
  const [zoom, setZoom] = useState(1)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)

  // OT-2 fallback for backward compatibility
  const config = deckConfig || {
    slotCount: 12,
    gridRows: 4,
    gridCols: 3,
    slotWidth: 200,
    slotHeight: 120,
    margin: 50,
    svgWidth: 800,
    svgHeight: 600,
    slotNamingScheme: 'numeric',
    trashSlot: '12',
    stagingGap: 0
  }

  // Calculate slot position based on robot type
  const getSlotPosition = (slotLabel) => {
    if (!slotLabel) return { x: 0, y: 0 }

    if (config.slotNamingScheme === 'coordinate') {
      // Flex: parse "A1" format
      const row = slotLabel.charCodeAt(0) - 'A'.charCodeAt(0)
      const col = parseInt(slotLabel.slice(1)) - 1
      const extraGap = col === 3 ? config.stagingGap : 0
      return {
        x: config.margin + col * config.slotWidth + extraGap,
        y: config.margin + row * config.slotHeight
      }
    } else {
      // OT-2: existing numeric logic
      const slotNum = parseInt(slotLabel)
      const slot_index = slotNum - 1
      const row = 3 - Math.floor(slot_index / 3)
      const col = slot_index % 3
      return {
        x: config.margin + col * config.slotWidth,
        y: config.margin + row * config.slotHeight
      }
    }
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5))
  const handleReset = () => setZoom(1)

  // Reset playback when new simulation data arrives
  useEffect(() => {
    setIsPlaying(false)
  }, [steps])

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
    // Check for 96-channel in name
    if (pipetteName.toLowerCase().includes('96')) return 96
    if (pipetteName.toLowerCase().includes('multi')) return 8
    return 1
  }

  const expandWellTargets = (labwareLabel, wellId, channels) => {
    const info = getLabwareInfo(labwareLabel)
    if (!info) return [wellId]

    // Single-channel: just the target well
    if (channels === 1) return [wellId]

    // Reservoir with multichannel: special handling (keep existing)
    const isReservoir = labwareLabel.toLowerCase().includes('reservoir')
    if (isReservoir) return [wellId]

    const match = wellId.match(/^([A-Z]+)(\d+)$/)
    if (!match) return [wellId]

    const targetRow = match[1]
    const targetCol = match[2]

    // 96-channel: expand to ALL wells (entire plate)
    if (channels === 96) {
      const allWells = []
      for (const row of info.rowLetters) {
        for (let col = 1; col <= info.cols; col++) {
          const wellId = `${row}${col}`
          if (info.wellMap[wellId]) {
            allWells.push(wellId)
          }
        }
      }
      return allWells
    }

    // 8-channel: existing logic for 8 or 16 rows
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

  // Generate multiple tip positions for multichannel pipette on single-well reservoir
  const getMultichannelReservoirPositions = (baseCoords, channels = 8) => {
    // Spread tips vertically across the reservoir well
    // Reservoir wells are tall troughs - tips are spaced ~9mm apart (roughly 7px in our scale)
    const tipSpacing = 7
    const totalHeight = tipSpacing * (channels - 1)
    const startY = baseCoords.y - totalHeight / 2

    return Array.from({ length: channels }, (_, i) => ({
      x: baseCoords.x,
      y: startY + i * tipSpacing
    }))
  }

  // Check if labware is a reservoir (single row of troughs)
  // For reservoirs, multichannel tips all go into the same trough column
  const isReservoirLabware = (labwareLabel) => {
    const info = getLabwareInfo(labwareLabel)
    if (!info) return false
    const isReservoir = labwareLabel.toLowerCase().includes('reservoir')
    // Reservoirs have 1 row (all troughs in a single row: A1, A2, ... A12)
    return isReservoir && info.rows === 1
  }

  // Check if labware is trash
  const isTrashLabware = (labwareLabel) => {
    return labwareLabel?.toLowerCase().includes('trash')
  }

  // Get fixed coordinates for trash
  const getTrashCoordinates = () => {
    if (config.trashSlot) {
      // OT-2: trash in specific slot
      const pos = getSlotPosition(config.trashSlot)
      return {
        x: pos.x + config.slotWidth / 2 - 5,
        y: pos.y + config.slotHeight / 2
      }
    } else {
      // Flex: waste chute in margin (fixed position)
      return {
        x: config.margin + config.slotWidth * config.gridCols + 20,
        y: config.margin + config.slotHeight * config.gridRows - 30
      }
    }
  }

  // Render triangle indicator
  const renderTriangle = (type, x, y, key) => {
    const configs = {
      aspirate: { color: '#00ff41', direction: 'down' },
      dispense: { color: '#e6b800', direction: 'up' },
      distribute: { color: '#00ff41', direction: 'down' },
      transfer: { color: '#00ff41', direction: 'down' },
      pick_up_tip: { color: '#e0f0e0', direction: 'up' },
      drop_tip: { color: '#2d5e2d', direction: 'down' }
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

    // Determine what to show based on step type
    // - aspirate/pick_up_tip: show source only (taking from a location)
    // - dispense/drop_tip: show dest only (putting to a location)
    // - transfer/distribute: skip - these are summary steps,
    //   the actual aspirate/dispense sub-steps will show the real action
    const sourceTypes = ['aspirate', 'pick_up_tip']
    const destTypes = ['dispense', 'drop_tip']
    const skipTypes = ['transfer', 'distribute']

    const showSource = sourceTypes.includes(step.type)
    const showDest = destTypes.includes(step.type)

    // Skip transfer/distribute - they're summary steps
    if (skipTypes.includes(step.type)) {
      return null
    }

    // Handle source well (aspirate, pick_up_tip)
    if (showSource && step.source?.labware && step.source?.well) {
      // Check for multichannel + single-well reservoir special case
      const isMulti = channels >= 8
      if (isMulti && isReservoirLabware(step.source.labware)) {
        const baseCoords = getWellCoordinates(step.source.labware, step.source.well)
        if (baseCoords) {
          const positions = getMultichannelReservoirPositions(baseCoords, channels)
          positions.forEach((pos, i) => {
            indicators.push(renderTriangle(step.type, pos.x - 6, pos.y - 8, `source-${step.idx}-tip${i}`))
          })
        }
      } else {
        const wells = expandWellTargets(step.source.labware, step.source.well, channels)
        for (const wellId of wells) {
          const coords = getWellCoordinates(step.source.labware, wellId)
          if (coords) {
            indicators.push(renderTriangle(step.type, coords.x - 6, coords.y - 8, `source-${step.idx}-${wellId}`))
          }
        }
      }
    }

    // Handle destination well (dispense, drop_tip)
    if (showDest && step.dest?.labware && step.dest?.well) {
      // Special case: dropping tip to trash
      if (isTrashLabware(step.dest.labware)) {
        const trashCoords = getTrashCoordinates()
        indicators.push(renderTriangle('drop_tip', trashCoords.x - 6, trashCoords.y - 8, `dest-${step.idx}-trash`))
      }
      // Check for multichannel + reservoir special case
      else {
        const isMulti = channels >= 8
        if (isMulti && isReservoirLabware(step.dest.labware)) {
          const baseCoords = getWellCoordinates(step.dest.labware, step.dest.well)
          if (baseCoords) {
            const positions = getMultichannelReservoirPositions(baseCoords, channels)
            positions.forEach((pos, i) => {
              indicators.push(renderTriangle(step.type, pos.x - 6, pos.y - 8, `dest-${step.idx}-tip${i}`))
            })
          }
        } else {
          const wells = expandWellTargets(step.dest.labware, step.dest.well, channels)
          for (const wellId of wells) {
            const coords = getWellCoordinates(step.dest.labware, wellId)
            if (coords) {
              indicators.push(renderTriangle(step.type, coords.x - 6, coords.y - 8, `dest-${step.idx}-${wellId}`))
            }
          }
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
            indicators.push(renderModulePulse(slot, `module-${step.idx}`))
            break
          }
        }
      }
    }

    // Handle move_labware (gripper moves)
    if (step.type === 'move_labware' && step.sourceSlot && step.destSlot) {
      const sourcePos = getSlotPosition(step.sourceSlot)
      const destPos = getSlotPosition(step.destSlot)

      // Calculate arrow path
      const startX = sourcePos.x + config.slotWidth / 2
      const startY = sourcePos.y + config.slotHeight / 2
      const endX = destPos.x + config.slotWidth / 2
      const endY = destPos.y + config.slotHeight / 2

      // Dashed amber arrow
      indicators.push(
        <g key={`move-${step.idx}`}>
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#e6b800" />
            </marker>
          </defs>
          <line
            x1={startX}
            y1={startY}
            x2={endX}
            y2={endY}
            stroke="#e6b800"
            strokeWidth="3"
            strokeDasharray="8,4"
            markerEnd="url(#arrowhead)"
            opacity="0.8"
          />
          {/* Pulse borders on source and dest slots */}
          <rect
            x={sourcePos.x}
            y={sourcePos.y}
            width={config.slotWidth - 10}
            height={config.slotHeight - 10}
            fill="none"
            stroke="#e6b800"
            strokeWidth="3"
            opacity="0.6"
            className="animate-pulse"
          />
          <rect
            x={destPos.x}
            y={destPos.y}
            width={config.slotWidth - 10}
            height={config.slotHeight - 10}
            fill="none"
            stroke="#e6b800"
            strokeWidth="3"
            opacity="0.6"
            className="animate-pulse"
          />
        </g>
      )
    }

    return indicators
  }

  // Render module pulse animation
  const renderModulePulse = (slotLabel, key) => {
    const pos = getSlotPosition(slotLabel)
    return (
      <rect
        key={key}
        x={pos.x}
        y={pos.y}
        width={config.slotWidth - 10}
        height={config.slotHeight - 10}
        fill="none"
        stroke="#c8a000"
        strokeWidth="3"
        opacity="0.6"
        className="animate-pulse"
      />
    )
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider">Deck Layout</h2>
        <div className="flex gap-0.5">
          <button onClick={handleZoomOut} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost hover:text-text-secondary transition-colors" title="Zoom Out">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={handleReset} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost hover:text-text-secondary transition-colors" title="Reset Zoom">
            <Maximize2 className="w-4 h-4" />
          </button>
          <button onClick={handleZoomIn} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost hover:text-text-secondary transition-colors" title="Zoom In">
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Playback Controls */}
      {steps.length > 0 && (
        <div className="flex items-center gap-2 mb-5 p-3 bg-surface-2 rounded-lg border border-edge">
          <button
            onClick={handlePlayPause}
            className="p-2 rounded-md hover:opacity-90 transition-colors"
            style={{ background: '#00ff41', color: '#0a0d0a' }}
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>

          <div className="flex gap-0.5">
            <button onClick={handleStepBackward} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost transition-colors" title="Step Backward" disabled={currentStepIndex <= 0}>
              <SkipBack size={14} />
            </button>
            <button onClick={handleStepForward} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost transition-colors" title="Step Forward" disabled={currentStepIndex >= steps.length - 1}>
              <SkipForward size={14} />
            </button>
            <button onClick={handleResetAnimation} className="p-1.5 hover:bg-surface-3 rounded text-text-ghost transition-colors" title="Reset">
              <RotateCcw size={14} />
            </button>
          </div>

          <div className="text-xs text-text-ghost ml-auto font-mono">
            {currentStepIndex >= 0
              ? `${currentStepIndex + 1} / ${steps.length}`
              : `${steps.length} steps`
            }
          </div>
        </div>
      )}

      {/* Current Step Indicator */}
      {currentStepIndex >= 0 && currentStepIndex < steps.length && (
        <div className="mb-3 px-4 py-2.5 bg-surface-1 rounded-lg border border-matrix/20 flex items-center gap-3 font-mono">
          <span className="text-matrix text-sm">
            {{ aspirate: '↑', dispense: '↓', pick_up_tip: '◆', drop_tip: '◇', mix: '↻', 'module.set_temperature': '○', move_labware: '→' }[steps[currentStepIndex].type] || '·'}
          </span>
          <span className="text-xs text-text-ghost">{currentStepIndex + 1}</span>
          <span className="text-xs text-text-tertiary">{steps[currentStepIndex].type}</span>
          <span className="text-sm text-text-primary truncate">{steps[currentStepIndex].metadata?.text || 'No description'}</span>
        </div>
      )}

      {/* SVG Display */}
      <div className="border border-edge rounded-lg overflow-auto bg-surface-2 p-4">
        <div
          className="transition-transform origin-top-left relative"
          style={{ transform: `scale(${zoom})` }}
        >
          <div dangerouslySetInnerHTML={{ __html: deckSvg }} />
          <svg
            width={config.svgWidth}
            height={config.svgHeight}
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
        <div className="mt-5 grid grid-cols-2 gap-3 text-xs font-mono">
          <div className="bg-surface-2 border border-edge p-3 rounded-lg">
            <span className="text-text-ghost">Slots</span>
            <span className="ml-2 text-text-primary">{deckLayout.slots?.length || config.slotCount}</span>
          </div>
          <div className="bg-surface-2 border border-edge p-3 rounded-lg">
            <span className="text-text-ghost">Occupied</span>
            <span className="ml-2 text-text-primary">{deckLayout.occupied?.length || 0}</span>
          </div>
        </div>
      )}

      {/* Color Legend */}
      <div className="mt-5 flex flex-wrap gap-4 text-xs text-text-ghost">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-matrix-warm/20 border border-matrix-warm/50 rounded-sm"></div>
          <span>Modules</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-matrix/20 border border-matrix/50 rounded-sm"></div>
          <span>Tipracks</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-matrix-dim/20 border border-matrix-dim/50 rounded-sm"></div>
          <span>Labware</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-red-500/20 border border-red-400/50 rounded-sm"></div>
          <span>Trash</span>
        </div>
        {robotModel === 'Flex' && (
          <>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 border border-dashed border-matrix-dim/50 rounded-sm"></div>
              <span>Staging</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 border border-matrix-amber/50 rounded-sm" style={{background: 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(230,184,0,0.3) 2px, rgba(230,184,0,0.3) 4px)'}}></div>
              <span>Gripper</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
