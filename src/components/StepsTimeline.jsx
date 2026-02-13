import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Filter, Download } from 'lucide-react'

const STEP_ICONS = {
  aspirate: '↑',
  dispense: '↓',
  pick_up_tip: '◆',
  drop_tip: '◇',
  mix: '↻',
  'module.set_temperature': '○',
  move_labware: '→',
  other: '·'
}

const STEP_ACCENTS = {
  aspirate: 'border-l-matrix',
  dispense: 'border-l-matrix-amber',
  pick_up_tip: 'border-l-[#e0f0e0]',
  drop_tip: 'border-l-green-900',
  mix: 'border-l-matrix-teal',
  'module.set_temperature': 'border-l-matrix-warm',
  move_labware: 'border-l-matrix-amber',
  other: 'border-l-green-800'
}

export default function StepsTimeline({ steps, currentStepIndex = -1, onStepClick }) {
  const [filter, setFilter] = useState('all')
  const [expandedSteps, setExpandedSteps] = useState(new Set())
  const stepRefs = useRef({})
  const containerRef = useRef(null)
  const userClickedRef = useRef(false)

  const handleStepClick = (idx) => {
    userClickedRef.current = true
    onStepClick?.(idx)
  }

  useEffect(() => {
    if (currentStepIndex >= 0 && stepRefs.current[currentStepIndex] && userClickedRef.current) {
      const container = containerRef.current
      const stepElement = stepRefs.current[currentStepIndex]

      if (container && stepElement) {
        stepElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'nearest'
        })
      }

      userClickedRef.current = false
    }
  }, [currentStepIndex])

  const filteredSteps = filter === 'all'
    ? steps
    : steps.filter(step => step.type === filter)

  const stepTypes = [...new Set(steps.map(s => s.type))]

  const toggleExpand = (idx) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx)
    } else {
      newExpanded.add(idx)
    }
    setExpandedSteps(newExpanded)
  }

  const exportToCSV = () => {
    const headers = ['Step', 'Type', 'Description']
    const rows = steps.map(step => [
      step.idx,
      step.type,
      step.metadata?.text || ''
    ])

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'protocol_steps.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider">
          Steps <span className="text-text-ghost">{filteredSteps.length}</span>
        </h2>
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-2.5 py-1 bg-surface-2 border border-edge rounded-md text-xs text-text-secondary focus:outline-none focus:border-edge-active font-mono"
          >
            <option value="all">all</option>
            {stepTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          <button
            onClick={exportToCSV}
            className="px-2.5 py-1 bg-surface-3 hover:bg-surface-4 text-text-secondary rounded-md text-xs flex items-center gap-1.5 transition-colors font-mono"
          >
            <Download className="w-3 h-3" />
            csv
          </button>
        </div>
      </div>

      {/* Steps List */}
      <div ref={containerRef} className="space-y-1 max-h-96 overflow-y-auto">
        {filteredSteps.length === 0 ? (
          <p className="text-text-ghost text-center py-8 text-xs font-mono">No steps to display</p>
        ) : (
          filteredSteps.map((step, index) => (
            <div
              key={step.idx}
              ref={(el) => (stepRefs.current[index] = el)}
              onClick={() => handleStepClick(index)}
              className={`border-l-2 rounded-r-lg px-4 py-2.5 transition-colors cursor-pointer ${
                index === currentStepIndex
                  ? 'border-l-matrix bg-surface-3'
                  : `${STEP_ACCENTS[step.type] || STEP_ACCENTS.other} bg-transparent hover:bg-surface-2`
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="font-mono text-sm text-text-ghost w-4 text-center">{STEP_ICONS[step.type] || STEP_ICONS.other}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-text-ghost">{step.idx}</span>
                      <span className="text-xs text-text-tertiary font-mono">{step.type}</span>
                    </div>
                    <p className="text-sm mt-0.5 text-text-secondary truncate">{step.metadata?.text || 'No description'}</p>
                  </div>
                </div>
                {(step.pipette || step.volumeUl || step.source || step.dest) && (
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleExpand(step.idx) }}
                    className="p-1 hover:bg-surface-4 rounded transition-colors flex-shrink-0"
                  >
                    {expandedSteps.has(step.idx) ? (
                      <ChevronUp className="w-3.5 h-3.5 text-text-ghost" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-text-ghost" />
                    )}
                  </button>
                )}
              </div>

              {/* Expanded Details */}
              {expandedSteps.has(step.idx) && (
                <div className="mt-2 pt-2 border-t border-edge text-xs font-mono text-text-tertiary space-y-1 ml-7">
                  {step.pipette && (
                    <div><span className="text-text-ghost">pipette</span> {step.pipette}</div>
                  )}
                  {step.volumeUl && (
                    <div><span className="text-text-ghost">volume</span> {step.volumeUl} µL</div>
                  )}
                  {step.source && (
                    <div><span className="text-text-ghost">source</span> {step.source.labware} {step.source.well}</div>
                  )}
                  {step.dest && (
                    <div><span className="text-text-ghost">dest</span> {step.dest.labware} {step.dest.well}</div>
                  )}
                  {step.flowRateUlS && (
                    <div><span className="text-text-ghost">flow</span> {step.flowRateUlS} µL/s</div>
                  )}
                  {step.targetC && (
                    <div><span className="text-text-ghost">temp</span> {step.targetC}°C</div>
                  )}
                  {step.sourceSlot && (
                    <div><span className="text-text-ghost">from</span> {step.sourceSlot}</div>
                  )}
                  {step.destSlot && (
                    <div><span className="text-text-ghost">to</span> {step.destSlot}</div>
                  )}
                  {step.useGripper && (
                    <div><span className="text-text-ghost">gripper</span> yes</div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Step Type Summary */}
      <div className="mt-5 pt-5 border-t border-edge flex flex-wrap gap-x-4 gap-y-1 text-xs font-mono">
        {stepTypes.map(type => (
          <div key={type} className="flex items-center gap-2 text-text-ghost">
            <span>{STEP_ICONS[type] || '·'}</span>
            <span>{type}</span>
            <span className="text-text-secondary">{steps.filter(s => s.type === type).length}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
