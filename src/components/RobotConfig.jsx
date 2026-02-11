import { useState } from 'react'
import { Settings, ChevronDown, ChevronUp } from 'lucide-react'

export default function RobotConfig({ config }) {
  const [expandedSections, setExpandedSections] = useState(new Set(['pipettes']))

  const toggleSection = (section) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const Section = ({ title, children, id }) => (
    <div className="border border-edge rounded-lg mb-3 overflow-hidden">
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-surface-2 transition-colors text-text-secondary"
      >
        <span className="font-mono text-xs uppercase tracking-wider">{title}</span>
        {expandedSections.has(id) ? (
          <ChevronUp className="w-3.5 h-3.5 text-text-ghost" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-text-ghost" />
        )}
      </button>
      {expandedSections.has(id) && (
        <div className="px-4 pb-4 border-t border-edge">
          {children}
        </div>
      )}
    </div>
  )

  const Field = ({ label, value }) => (
    <div className="flex justify-between py-1">
      <span className="text-text-ghost font-mono text-xs">{label}</span>
      <span className="text-text-secondary font-mono text-xs">{value}</span>
    </div>
  )

  return (
    <div className="card p-6">
      <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider mb-5">
        Configuration
      </h2>

      {/* Robot Info */}
      <div className="bg-surface-2 border border-edge rounded-lg p-4 mb-5">
        <Field label="model" value={config.robotModel || 'Unknown'} />
        <Field label="api" value={config.apiLevel || '2.x'} />
      </div>

      {/* Pipettes Section */}
      <Section title={`Pipettes ${config.pipettes?.length || 0}`} id="pipettes">
        {config.pipettes && config.pipettes.length > 0 ? (
          <div className="space-y-3 pt-3">
            {config.pipettes.map((pipette, idx) => (
              <div key={idx} className="bg-surface-2 rounded-lg p-3">
                <div className="font-mono text-xs text-text-primary mb-2">
                  {pipette.name}
                </div>
                <div className="space-y-0.5">
                  <Field label="mount" value={pipette.mount} />
                  <Field label="channels" value={pipette.channels} />
                  <Field label="range" value={`${pipette.minVolumeUl}–${pipette.maxVolumeUl} µL`} />
                </div>
                {pipette.tiprackLoadNames && pipette.tiprackLoadNames.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-edge">
                    <div className="text-text-ghost font-mono text-xs mb-1.5">tipracks</div>
                    <div className="flex flex-wrap gap-1">
                      {pipette.tiprackLoadNames.map((tiprack, i) => (
                        <span key={i} className="bg-surface-3 border border-edge px-2 py-0.5 rounded text-xs font-mono text-text-tertiary">
                          {tiprack}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-text-ghost text-xs font-mono pt-3">No pipettes configured</p>
        )}
      </Section>

      {/* Modules Section */}
      <Section title={`Modules ${config.modules?.length || 0}`} id="modules">
        {config.modules && config.modules.length > 0 ? (
          <div className="space-y-3 pt-3">
            {config.modules.map((module, idx) => (
              <div key={idx} className="bg-surface-2 rounded-lg p-3">
                <div className="font-mono text-xs text-text-primary mb-2">
                  {module.moduleType}
                </div>
                <div className="space-y-0.5">
                  <Field label="slot" value={module.slot} />
                  <Field label="model" value={module.model} />
                </div>
                {module.state && Object.keys(module.state).length > 0 && (
                  <div className="mt-2 pt-2 border-t border-edge space-y-0.5">
                    {module.state.targetTemperatureC && (
                      <Field label="temp" value={`${module.state.targetTemperatureC}°C`} />
                    )}
                    {module.state.speedRpm && (
                      <Field label="speed" value={`${module.state.speedRpm} RPM`} />
                    )}
                    {module.state.status && (
                      <Field label="status" value={module.state.status} />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-text-ghost text-xs font-mono pt-3">No modules configured</p>
        )}
      </Section>

      {/* Labware Section */}
      <Section title={`Labware ${config.labware?.length || 0}`} id="labware">
        {config.labware && config.labware.length > 0 ? (
          <div className="space-y-2 pt-3">
            {config.labware.map((labware, idx) => (
              <div key={idx} className="bg-surface-2 rounded-lg p-3">
                <div className="font-mono text-xs text-text-primary mb-1">
                  {labware.label}
                </div>
                <div className="space-y-0.5">
                  <Field label="slot" value={labware.slot} />
                  <Field label="load" value={labware.loadName} />
                  {labware.parent && <Field label="parent" value={labware.parent} />}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-text-ghost text-xs font-mono pt-3">No labware configured</p>
        )}
      </Section>
    </div>
  )
}
