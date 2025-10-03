import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileCode, Settings } from 'lucide-react'

export default function ProtocolInput({ onSimulate, loading }) {
  const [protocolFile, setProtocolFile] = useState(null)
  const [metadata, setMetadata] = useState('')
  const [showMetadata, setShowMetadata] = useState(false)

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setProtocolFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/x-python': ['.py'],
    },
    multiple: false,
  })

  const handleSimulate = () => {
    if (!protocolFile) return

    const formData = new FormData()
    formData.append('protocol_file', protocolFile)

    if (metadata.trim()) {
      formData.append('metadata', metadata)
    }

    onSimulate(formData)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <FileCode className="w-5 h-5" />
          Protocol Input
        </h2>
        <button
          onClick={() => setShowMetadata(!showMetadata)}
          className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
        >
          <Settings className="w-4 h-4" />
          {showMetadata ? 'Hide' : 'Show'} Metadata
        </button>
      </div>

      {/* File Upload */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
          ${protocolFile ? 'bg-green-50 border-green-400' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        {protocolFile ? (
          <div>
            <p className="text-green-700 font-medium">{protocolFile.name}</p>
            <p className="text-sm text-gray-500 mt-1">
              {(protocolFile.size / 1024).toFixed(2)} KB
            </p>
          </div>
        ) : (
          <div>
            <p className="text-gray-600">
              {isDragActive ? 'Drop the protocol file here' : 'Drag & drop a protocol file here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">or click to browse (.py files only)</p>
          </div>
        )}
      </div>

      {/* Metadata JSON (optional) */}
      {showMetadata && (
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Metadata (Optional JSON)
          </label>
          <textarea
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
            placeholder='{"protocolName": "My Protocol", "author": "Lab Tech"}'
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            rows="4"
          />
        </div>
      )}

      {/* Simulate Button */}
      <button
        onClick={handleSimulate}
        disabled={!protocolFile || loading}
        className={`mt-4 w-full py-3 px-4 rounded-lg font-medium transition-colors
          ${!protocolFile || loading
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Simulating...
          </span>
        ) : (
          'Simulate Protocol'
        )}
      </button>
    </div>
  )
}
