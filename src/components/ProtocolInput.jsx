import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileCode, Settings } from 'lucide-react'

export default function ProtocolInput({ onSimulate, onFileSelected, loading, hero, extractingParams }) {
  const [protocolFile, setProtocolFile] = useState(null)
  const [metadata, setMetadata] = useState('')
  const [showMetadata, setShowMetadata] = useState(false)

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setProtocolFile(file)
      if (onFileSelected) {
        onFileSelected(file)
      }
    }
  }, [onFileSelected])

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
    <div className={hero ? 'card p-8' : 'card p-6'}>
      {!hero && (
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider">
            Protocol Input
          </h2>
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="text-xs text-text-ghost hover:text-text-secondary flex items-center gap-1.5 transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            {showMetadata ? 'Hide' : 'Show'} Metadata
          </button>
        </div>
      )}

      {/* File Upload */}
      <div
        {...getRootProps()}
        className={`border border-dashed rounded-lg text-center cursor-pointer transition-all
          ${hero ? 'p-16' : 'p-10'}
          ${isDragActive ? 'border-matrix/40 bg-matrix/5' : 'border-edge hover:border-edge-hover'}
          ${protocolFile ? 'border-matrix/30 bg-matrix/5' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className={`${hero ? 'w-10 h-10 mb-4' : 'w-8 h-8 mb-3'} mx-auto ${protocolFile ? 'text-matrix' : 'text-text-ghost'}`} />
        {protocolFile ? (
          <div>
            <p className={`text-text-primary font-mono ${hero ? 'text-base' : 'text-sm'}`}>{protocolFile.name}</p>
            <p className="text-xs text-text-ghost mt-1 font-mono">
              {(protocolFile.size / 1024).toFixed(2)} KB
            </p>
          </div>
        ) : (
          <div>
            <p className={`text-text-secondary ${hero ? 'text-base' : 'text-sm'}`}>
              {isDragActive ? 'Drop the protocol file here' : 'Drop your protocol file here'}
            </p>
            <p className="text-xs text-text-ghost mt-2">or click to browse</p>
          </div>
        )}
      </div>

      {/* Parameter extraction loading */}
      {extractingParams && (
        <div className="mt-3 flex items-center gap-2 text-xs text-text-ghost font-mono">
          <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Detecting runtime parameters...
        </div>
      )}

      {/* Metadata JSON (optional) */}
      {!hero && showMetadata && (
        <div className="mt-5">
          <label className="block text-xs font-mono text-text-ghost uppercase tracking-wider mb-2">
            Metadata JSON
          </label>
          <textarea
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
            placeholder='{"protocolName": "My Protocol", "author": "Lab Tech"}'
            className="w-full px-3 py-2.5 bg-surface-2 border border-edge rounded-lg focus:outline-none focus:border-edge-active font-mono text-sm text-text-primary placeholder-text-ghost"
            rows="4"
          />
        </div>
      )}

      {/* Simulate Button */}
      <button
        onClick={handleSimulate}
        disabled={!protocolFile || loading}
        className={`mt-5 w-full py-2.5 px-4 rounded-lg text-sm font-medium transition-all
          ${!protocolFile || loading
            ? 'bg-surface-3 cursor-not-allowed'
            : 'hover:opacity-90'
          }
        `}
        style={!protocolFile || loading
          ? { color: '#2d5e2d' }
          : { background: '#00ff41', color: '#0a0d0a' }
        }
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
