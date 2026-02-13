import { useState } from 'react'
import { Sliders, ToggleLeft, ToggleRight, FileText, Hash, Type } from 'lucide-react'

export default function RuntimeParameters({ parameters, values, csvFiles, onValuesChange, onCsvFileChange }) {
  const handleChange = (variableName, value) => {
    onValuesChange({ ...values, [variableName]: value })
  }

  const handleCsvChange = (variableName, file) => {
    onCsvFileChange({ ...csvFiles, [variableName]: file })
  }

  const renderField = (param) => {
    switch (param.type) {
      case 'bool':
        return (
          <button
            type="button"
            onClick={() => handleChange(param.variable_name, !values[param.variable_name])}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
              values[param.variable_name]
                ? 'border-matrix/30 bg-matrix/10 text-matrix'
                : 'border-edge bg-surface-2 text-text-ghost'
            }`}
          >
            {values[param.variable_name]
              ? <ToggleRight className="w-5 h-5" />
              : <ToggleLeft className="w-5 h-5" />}
            <span className="text-sm font-mono">
              {values[param.variable_name] ? 'On' : 'Off'}
            </span>
          </button>
        )

      case 'int':
      case 'float':
        if (param.choices) {
          return (
            <select
              value={values[param.variable_name]}
              onChange={e => handleChange(
                param.variable_name,
                param.type === 'int' ? parseInt(e.target.value) : parseFloat(e.target.value)
              )}
              className="w-full px-3 py-2 bg-surface-2 border border-edge rounded-lg focus:outline-none focus:border-edge-active font-mono text-sm text-text-primary"
            >
              {param.choices.map(c => (
                <option key={c.value} value={c.value}>{c.display_name}</option>
              ))}
            </select>
          )
        }
        return (
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={values[param.variable_name] ?? ''}
              min={param.minimum}
              max={param.maximum}
              step={param.type === 'float' ? 0.1 : 1}
              onChange={e => {
                const raw = e.target.value
                if (raw === '') return
                handleChange(
                  param.variable_name,
                  param.type === 'int' ? parseInt(raw) : parseFloat(raw)
                )
              }}
              className="w-full px-3 py-2 bg-surface-2 border border-edge rounded-lg focus:outline-none focus:border-edge-active font-mono text-sm text-text-primary"
            />
            {param.unit && (
              <span className="text-xs text-text-ghost font-mono whitespace-nowrap">
                {param.unit}
              </span>
            )}
          </div>
        )

      case 'str':
        if (param.choices) {
          return (
            <select
              value={values[param.variable_name]}
              onChange={e => handleChange(param.variable_name, e.target.value)}
              className="w-full px-3 py-2 bg-surface-2 border border-edge rounded-lg focus:outline-none focus:border-edge-active font-mono text-sm text-text-primary"
            >
              {param.choices.map(c => (
                <option key={c.value} value={c.value}>{c.display_name}</option>
              ))}
            </select>
          )
        }
        return (
          <input
            type="text"
            value={values[param.variable_name] ?? ''}
            onChange={e => handleChange(param.variable_name, e.target.value)}
            className="w-full px-3 py-2 bg-surface-2 border border-edge rounded-lg focus:outline-none focus:border-edge-active font-mono text-sm text-text-primary"
          />
        )

      case 'csv_file':
        return (
          <div>
            <input
              type="file"
              accept=".csv"
              onChange={e => handleCsvChange(param.variable_name, e.target.files[0])}
              className="hidden"
              id={`csv-${param.variable_name}`}
            />
            <label
              htmlFor={`csv-${param.variable_name}`}
              className="flex items-center gap-2 px-3 py-2 bg-surface-2 border border-dashed border-edge rounded-lg cursor-pointer hover:border-edge-hover transition-colors"
            >
              <FileText className="w-4 h-4 text-text-ghost" />
              <span className="text-xs font-mono text-text-secondary">
                {csvFiles[param.variable_name]?.name || 'Choose CSV file...'}
              </span>
            </label>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-5">
        <Sliders className="w-4 h-4 text-text-ghost" />
        <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider">
          Runtime Parameters
        </h2>
      </div>

      <div className="space-y-4">
        {parameters.map(param => (
          <div key={param.variable_name} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-sm text-text-primary">{param.display_name}</label>
              {param.minimum != null && param.maximum != null && (
                <span className="text-xs text-text-ghost font-mono">
                  {param.minimum}&ndash;{param.maximum}
                </span>
              )}
            </div>
            {param.description && (
              <p className="text-xs text-text-ghost">{param.description}</p>
            )}
            {renderField(param)}
          </div>
        ))}
      </div>
    </div>
  )
}
