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
    <div className="border border-gray-200 rounded-lg mb-3">
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium">{title}</span>
        {expandedSections.has(id) ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>
      {expandedSections.has(id) && (
        <div className="p-3 pt-0 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  )

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5" />
        Robot Configuration
      </h2>

      {/* Robot Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm">
        <div className="flex justify-between mb-1">
          <span className="text-gray-600">Robot Model:</span>
          <span className="font-semibold">{config.robotModel || 'Unknown'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">API Level:</span>
          <span className="font-semibold">{config.apiLevel || '2.x'}</span>
        </div>
      </div>

      {/* Pipettes Section */}
      <Section title={`Pipettes (${config.pipettes?.length || 0})`} id="pipettes">
        {config.pipettes && config.pipettes.length > 0 ? (
          <div className="space-y-3">
            {config.pipettes.map((pipette, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-3 text-sm">
                <div className="font-semibold text-blue-700 mb-2">
                  {pipette.name}
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Mount:</span>
                    <span className="font-medium capitalize">{pipette.mount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Channels:</span>
                    <span className="font-medium">{pipette.channels}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Volume Range:</span>
                    <span className="font-medium">{pipette.minVolumeUl} - {pipette.maxVolumeUl} µL</span>
                  </div>
                  {pipette.tiprackLoadNames && pipette.tiprackLoadNames.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-gray-600 mb-1">Compatible Tipracks:</div>
                      <div className="flex flex-wrap gap-1">
                        {pipette.tiprackLoadNames.map((tiprack, i) => (
                          <span key={i} className="bg-white px-2 py-0.5 rounded text-xs">
                            {tiprack}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No pipettes configured</p>
        )}
      </Section>

      {/* Modules Section */}
      <Section title={`Modules (${config.modules?.length || 0})`} id="modules">
        {config.modules && config.modules.length > 0 ? (
          <div className="space-y-3">
            {config.modules.map((module, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-3 text-sm">
                <div className="font-semibold text-purple-700 mb-2">
                  {module.moduleType}
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Slot:</span>
                    <span className="font-medium">{module.slot}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Model:</span>
                    <span className="font-medium">{module.model}</span>
                  </div>
                  {module.state && Object.keys(module.state).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-gray-600 mb-1">State:</div>
                      {module.state.targetTemperatureC && (
                        <div className="flex justify-between">
                          <span>Temperature:</span>
                          <span className="font-medium">{module.state.targetTemperatureC}°C</span>
                        </div>
                      )}
                      {module.state.speedRpm && (
                        <div className="flex justify-between">
                          <span>Speed:</span>
                          <span className="font-medium">{module.state.speedRpm} RPM</span>
                        </div>
                      )}
                      {module.state.status && (
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className="font-medium capitalize">{module.state.status}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No modules configured</p>
        )}
      </Section>

      {/* Labware Section */}
      <Section title={`Labware (${config.labware?.length || 0})`} id="labware">
        {config.labware && config.labware.length > 0 ? (
          <div className="space-y-2">
            {config.labware.map((labware, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-2 text-xs">
                <div className="font-semibold text-green-700 mb-1">
                  {labware.label}
                </div>
                <div className="space-y-0.5">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Slot:</span>
                    <span className="font-medium">{labware.slot}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Load Name:</span>
                    <span className="font-medium font-mono text-xs">{labware.loadName}</span>
                  </div>
                  {labware.parent && (
                    <div className="flex justify-between text-purple-600">
                      <span>Parent:</span>
                      <span className="font-medium">{labware.parent}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No labware configured</p>
        )}
      </Section>
    </div>
  )
}
