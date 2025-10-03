import { useState } from 'react'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

export default function DeckVisualization({ deckSvg, deckLayout }) {
  const [zoom, setZoom] = useState(1)
  const [selectedSlot, setSelectedSlot] = useState(null)

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5))
  const handleReset = () => setZoom(1)

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

      {/* SVG Display */}
      <div className="border border-gray-200 rounded-lg overflow-auto bg-gray-50 p-4">
        <div
          className="transition-transform origin-top-left"
          style={{ transform: `scale(${zoom})` }}
          dangerouslySetInnerHTML={{ __html: deckSvg }}
        />
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
      <div className="mt-4 flex gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-100 border border-blue-400 rounded"></div>
          <span>Modules</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-100 border border-gray-400 rounded"></div>
          <span>Labware</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 border border-green-400 rounded"></div>
          <span>Tipracks</span>
        </div>
      </div>
    </div>
  )
}
