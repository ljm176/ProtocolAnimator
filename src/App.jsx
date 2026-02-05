import { useState } from 'react'
import ProtocolInput from './components/ProtocolInput'
import DeckVisualization from './components/DeckVisualization'
import StepsTimeline from './components/StepsTimeline'
import RobotConfig from './components/RobotConfig'
import ValidationPanel from './components/ValidationPanel'
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

      // Parse response first to get error details
      const data = await response.json()
      console.log('Response data:', data)

      if (!response.ok) {
        // Extract detailed error message from backend
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">Opentrons Protocol Simulator</h1>
          <p className="text-blue-100 text-sm">Simulate and visualize your protocols without hardware</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-4">
        {/* Protocol Input */}
        <div className="mb-6">
          <ProtocolInput onSimulate={handleSimulate} loading={loading} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <div className="flex items-start gap-2">
              <strong className="font-semibold">Error:</strong>
              <div className="flex-1">
                <p className="whitespace-pre-wrap">{error}</p>
                <p className="text-sm text-red-600 mt-2">
                  💡 Check the browser console (F12) for more details
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Results Grid */}
        {simulationData && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Deck and Config */}
            <div className="lg:col-span-2 space-y-6">
              <DeckVisualization
                deckSvg={simulationData.deck_svg}
                deckLayout={simulationData.deck_layout}
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

            {/* Right Column - Config and Export */}
            <div className="space-y-6">
              <RobotConfig config={simulationData.robot_config} />
              <ExportDashboard
                artifactPaths={simulationData.artifact_paths}
                report={simulationData.report}
              />
            </div>
          </div>
        )}

        {/* Validation Panel */}
        {!simulationData && !loading && (
          <ValidationPanel />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white p-4 mt-12">
        <div className="container mx-auto text-center text-sm">
          <p>Opentrons Protocol Simulator v1.0.0</p>
          <p className="text-gray-400 mt-1">Static simulator using official Opentrons API</p>
        </div>
      </footer>
    </div>
  )
}

export default App
