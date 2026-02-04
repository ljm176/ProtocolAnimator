import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Filter, Download } from 'lucide-react'

const STEP_ICONS = {
  aspirate: '↓',
  dispense: '↑',
  pick_up_tip: '🔧',
  drop_tip: '🗑️',
  mix: '🔄',
  'module.set_temperature': '🌡️',
  other: '•'
}

const STEP_COLORS = {
  aspirate: 'bg-blue-50 border-blue-300 text-blue-700',
  dispense: 'bg-green-50 border-green-300 text-green-700',
  pick_up_tip: 'bg-yellow-50 border-yellow-300 text-yellow-700',
  drop_tip: 'bg-gray-50 border-gray-300 text-gray-700',
  mix: 'bg-purple-50 border-purple-300 text-purple-700',
  'module.set_temperature': 'bg-orange-50 border-orange-300 text-orange-700',
  other: 'bg-gray-50 border-gray-300 text-gray-600'
}

export default function StepsTimeline({ steps, currentStepIndex = -1, onStepClick }) {
  const [filter, setFilter] = useState('all')
  const [expandedSteps, setExpandedSteps] = useState(new Set())
  const stepRefs = useRef({})
  const containerRef = useRef(null)
  const userClickedRef = useRef(false)

  // Handle step click - mark as user-initiated
  const handleStepClick = (idx) => {
    userClickedRef.current = true
    onStepClick?.(idx)
  }

  // Auto-scroll only when user clicks a step manually
  useEffect(() => {
    if (currentStepIndex >= 0 && stepRefs.current[currentStepIndex] && userClickedRef.current) {
      const container = containerRef.current
      const stepElement = stepRefs.current[currentStepIndex]

      if (container && stepElement) {
        // Scroll within container only
        stepElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'nearest'
        })
      }

      userClickedRef.current = false // Reset flag after scroll
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
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Execution Steps ({filteredSteps.length})</h2>
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Steps</option>
            {stepTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          <button
            onClick={exportToCSV}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-1"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      {/* Steps List */}
      <div ref={containerRef} className="space-y-2 max-h-96 overflow-y-auto">
        {filteredSteps.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No steps to display</p>
        ) : (
          filteredSteps.map((step, index) => (
            <div
              key={step.idx}
              ref={(el) => (stepRefs.current[step.idx] = el)}
              onClick={() => handleStepClick(step.idx)}
              className={`border rounded-lg p-3 transition-all cursor-pointer ${
                step.idx === currentStepIndex
                  ? 'ring-2 ring-blue-500 bg-blue-50 shadow-lg'
                  : STEP_COLORS[step.type] || STEP_COLORS.other
              } hover:shadow-md`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-2xl">{STEP_ICONS[step.type] || STEP_ICONS.other}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold">#{step.idx}</span>
                      <span className="text-xs bg-white px-2 py-0.5 rounded">{step.type}</span>
                    </div>
                    <p className="text-sm mt-1">{step.metadata?.text || 'No description'}</p>
                  </div>
                </div>
                {(step.pipette || step.volumeUl || step.source || step.dest) && (
                  <button
                    onClick={() => toggleExpand(step.idx)}
                    className="p-1 hover:bg-white/50 rounded transition-colors"
                  >
                    {expandedSteps.has(step.idx) ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>

              {/* Expanded Details */}
              {expandedSteps.has(step.idx) && (
                <div className="mt-3 pt-3 border-t border-current/20 text-xs space-y-1">
                  {step.pipette && (
                    <div><span className="font-semibold">Pipette:</span> {step.pipette}</div>
                  )}
                  {step.volumeUl && (
                    <div><span className="font-semibold">Volume:</span> {step.volumeUl} µL</div>
                  )}
                  {step.source && (
                    <div><span className="font-semibold">Source:</span> {step.source.labware} - {step.source.well}</div>
                  )}
                  {step.dest && (
                    <div><span className="font-semibold">Destination:</span> {step.dest.labware} - {step.dest.well}</div>
                  )}
                  {step.flowRateUlS && (
                    <div><span className="font-semibold">Flow Rate:</span> {step.flowRateUlS} µL/s</div>
                  )}
                  {step.targetC && (
                    <div><span className="font-semibold">Target Temp:</span> {step.targetC}°C</div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Step Type Summary */}
      <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-2 text-xs">
        {stepTypes.slice(0, 6).map(type => (
          <div key={type} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded">
            <span className="flex items-center gap-1">
              <span>{STEP_ICONS[type] || '•'}</span>
              <span className="truncate">{type}</span>
            </span>
            <span className="font-semibold">{steps.filter(s => s.type === type).length}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
