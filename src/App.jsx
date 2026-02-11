import { useState } from 'react'
import ProtocolInput from './components/ProtocolInput'
import DeckVisualization from './components/DeckVisualization'
import StepsTimeline from './components/StepsTimeline'
import RobotConfig from './components/RobotConfig'
import ExportDashboard from './components/ExportDashboard'

function App() {
  const [simulationData, setSimulationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [currentStepIndex, setCurrentStepIndex] = useState(-1)

  const handleSimulate = async (formData) => {
    setLoading(true)
    setError(null)

    try {
      console.log('Sending simulation request...')
      const response = await fetch('/api/simulate', {
        method: 'POST',
        body: formData,
      })

      console.log('Response status:', response.status)

      const data = await response.json()
      console.log('Response data:', data)

      if (!response.ok) {
        const errorMessage = data.detail || data.message || 'Simulation failed'
        console.error('Simulation error:', errorMessage)
        throw new Error(errorMessage)
      }

      console.log('Simulation successful!')
      setSimulationData(data)
    } catch (err) {
      console.error('Error during simulation:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-0">
      {/* Header */}
      <header className="border-b border-edge">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <p className="font-mono text-xs text-text-ghost uppercase tracking-widest mb-1">Simulator</p>
          <h1 className="text-xl font-semibold text-gradient tracking-tight">
            Opentrons Protocol Simulator
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-10">
        {!simulationData ? (
          /* Landing — hero drop zone */
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="w-full max-w-xl">
              <ProtocolInput onSimulate={handleSimulate} loading={loading} hero />
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-8 w-full max-w-xl card px-5 py-4 border-red-500/20">
                <div className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-red-400">Error</p>
                    <p className="text-sm whitespace-pre-wrap mt-1 text-text-secondary">{error}</p>
                    <p className="text-xs text-text-ghost mt-2">
                      Check the browser console (F12) for more details
                    </p>
                  </div>
                </div>
              </div>
            )}

            <p className="mt-8 text-xs text-text-ghost font-mono">
              .py files only &middot; Opentrons API v2
            </p>
          </div>
        ) : (
          /* Results view */
          <>
            <div className="mb-10">
              <ProtocolInput onSimulate={handleSimulate} loading={loading} />
            </div>

            {error && (
              <div className="mb-10 card px-5 py-4 border-red-500/20">
                <div className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-red-400">Error</p>
                    <p className="text-sm whitespace-pre-wrap mt-1 text-text-secondary">{error}</p>
                    <p className="text-xs text-text-ghost mt-2">
                      Check the browser console (F12) for more details
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <DeckVisualization
                  deckSvg={simulationData.deck_svg}
                  deckLayout={simulationData.deck_layout}
                  deckConfig={simulationData.deck_config}
                  robotModel={simulationData.robot_config?.robotModel}
                  steps={simulationData.steps}
                  wellCoordinates={simulationData.well_coordinates}
                  pipettes={simulationData.robot_config?.pipettes || []}
                  currentStepIndex={currentStepIndex}
                  onStepChange={setCurrentStepIndex}
                />
                <StepsTimeline
                  steps={simulationData.steps}
                  currentStepIndex={currentStepIndex}
                  onStepClick={setCurrentStepIndex}
                />
              </div>

              <div className="space-y-6">
                <RobotConfig config={simulationData.robot_config} />
                <ExportDashboard
                  artifactPaths={simulationData.artifact_paths}
                  report={simulationData.report}
                />
              </div>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-edge mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8 flex items-center justify-between">
          <p className="text-xs text-text-ghost font-mono">v1.0.0</p>
          <p className="text-xs text-text-ghost">Static simulator &middot; Opentrons API</p>
        </div>
      </footer>
    </div>
  )
}

export default App
