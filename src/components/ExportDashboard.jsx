import { Download, FileJson, FileText, Image } from 'lucide-react'
import { useState } from 'react'

export default function ExportDashboard({ artifactPaths, report }) {
  const [showReport, setShowReport] = useState(false)

  const downloadArtifact = async (type) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${API_URL}/api/download/${type}`)
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
    { id: 'robot_json', name: 'robot.json', description: 'Robot configuration', icon: <FileJson className="w-3.5 h-3.5" /> },
    { id: 'steps_json', name: 'steps.json', description: 'Execution steps', icon: <FileJson className="w-3.5 h-3.5" /> },
    { id: 'deck_svg', name: 'deck.svg', description: 'Deck visualization', icon: <Image className="w-3.5 h-3.5" /> },
    { id: 'report', name: 'report.md', description: 'Summary report', icon: <FileText className="w-3.5 h-3.5" /> },
  ]

  return (
    <div className="card p-6">
      <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider mb-5">
        Export
      </h2>

      <div className="space-y-1">
        {artifacts.map(artifact => (
          <div
            key={artifact.id}
            className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-surface-2 transition-colors group"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <span className="text-text-ghost group-hover:text-text-secondary transition-colors">{artifact.icon}</span>
              <div className="min-w-0">
                <p className="font-mono text-xs text-text-primary">{artifact.name}</p>
                <p className="text-xs text-text-ghost">{artifact.description}</p>
              </div>
            </div>
            <button
              onClick={() => downloadArtifact(artifact.id)}
              className="p-1.5 hover:bg-surface-4 rounded transition-colors opacity-0 group-hover:opacity-100"
              title="Download"
            >
              <Download className="w-3.5 h-3.5 text-text-ghost" />
            </button>
          </div>
        ))}
      </div>

      {/* Report Preview */}
      {report && (
        <div className="mt-5">
          <button
            onClick={() => setShowReport(!showReport)}
            className="w-full text-left px-3 py-2 bg-surface-2 border border-edge hover:border-edge-hover rounded-lg transition-colors text-xs font-mono text-text-ghost"
          >
            {showReport ? 'hide' : 'show'} report preview
          </button>

          {showReport && (
            <div className="mt-2 p-3 bg-surface-2 rounded-lg border border-edge max-h-64 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono text-text-tertiary">{report}</pre>
            </div>
          )}
        </div>
      )}

      {/* Download All */}
      <div className="mt-5 pt-5 border-t border-edge">
        <button
          onClick={() => {
            artifacts.forEach(artifact => downloadArtifact(artifact.id))
          }}
          className="w-full py-2.5 px-4 rounded-lg hover:opacity-90 transition-colors text-sm font-medium"
          style={{ background: '#00ff41', color: '#0a0d0a' }}
        >
          Download All
        </button>
      </div>
    </div>
  )
}
