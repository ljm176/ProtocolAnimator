import { Download, FileJson, FileText, Image } from 'lucide-react'
import { useState } from 'react'

export default function ExportDashboard({ artifactPaths, report }) {
  const [showReport, setShowReport] = useState(false)

  const downloadArtifact = async (type) => {
    try {
      const response = await fetch(`/api/download/${type}`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      const fileNames = {
        robot_json: 'robot.json',
        steps_json: 'steps.json',
        deck_svg: 'deck.svg',
        report: 'report.md'
      }

      a.download = fileNames[type] || 'download'
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const artifacts = [
    {
      id: 'robot_json',
      name: 'Robot Config',
      description: 'Complete robot configuration',
      icon: <FileJson className="w-5 h-5" />,
      color: 'bg-blue-50 border-blue-300 text-blue-700'
    },
    {
      id: 'steps_json',
      name: 'Execution Steps',
      description: 'Ordered list of protocol steps',
      icon: <FileJson className="w-5 h-5" />,
      color: 'bg-green-50 border-green-300 text-green-700'
    },
    {
      id: 'deck_svg',
      name: 'Deck Layout',
      description: 'SVG visualization of deck',
      icon: <Image className="w-5 h-5" />,
      color: 'bg-purple-50 border-purple-300 text-purple-700'
    },
    {
      id: 'report',
      name: 'Summary Report',
      description: 'Markdown summary',
      icon: <FileText className="w-5 h-5" />,
      color: 'bg-orange-50 border-orange-300 text-orange-700'
    }
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Download className="w-5 h-5" />
        Export Artifacts
      </h2>

      <div className="space-y-3">
        {artifacts.map(artifact => (
          <div
            key={artifact.id}
            className={`border rounded-lg p-3 ${artifact.color}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex gap-3 flex-1">
                {artifact.icon}
                <div className="flex-1">
                  <h3 className="font-medium">{artifact.name}</h3>
                  <p className="text-xs opacity-80 mt-0.5">{artifact.description}</p>
                </div>
              </div>
              <button
                onClick={() => downloadArtifact(artifact.id)}
                className="p-2 hover:bg-white/50 rounded transition-colors"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Report Preview */}
      {report && (
        <div className="mt-4">
          <button
            onClick={() => setShowReport(!showReport)}
            className="w-full text-left px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded transition-colors text-sm font-medium"
          >
            {showReport ? 'Hide' : 'Show'} Report Preview
          </button>

          {showReport && (
            <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-200 max-h-64 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">{report}</pre>
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <button
          onClick={() => {
            artifacts.forEach(artifact => downloadArtifact(artifact.id))
          }}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Download All Artifacts
        </button>
      </div>
    </div>
  )
}
