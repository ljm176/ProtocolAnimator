import { AlertCircle, CheckCircle, Info } from 'lucide-react'

export default function ValidationPanel() {
  const tips = [
    {
      title: 'Protocol Structure',
      description: 'Ensure your protocol has a run() function that accepts a ProtocolContext parameter',
      icon: <Info className="w-5 h-5 text-blue-500" />
    },
    {
      title: 'API Level',
      description: 'Specify the API level in metadata: {"apiLevel": "2.14"}',
      icon: <Info className="w-5 h-5 text-blue-500" />
    },
    {
      title: 'Import Statement',
      description: 'Use: from opentrons import protocol_api',
      icon: <Info className="w-5 h-5 text-blue-500" />
    },
    {
      title: 'Metadata',
      description: 'Include protocol name, author, and description in metadata dictionary',
      icon: <CheckCircle className="w-5 h-5 text-green-500" />
    }
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <AlertCircle className="w-5 h-5 text-blue-600" />
        Protocol Guidelines
      </h2>

      <div className="space-y-3">
        {tips.map((tip, idx) => (
          <div key={idx} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0 mt-0.5">
              {tip.icon}
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">{tip.title}</h3>
              <p className="text-sm text-gray-600">{tip.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Example Protocol Structure:</h3>
        <pre className="text-xs bg-white p-3 rounded border border-blue-200 overflow-x-auto">
{`from opentrons import protocol_api

metadata = {
    'protocolName': 'My Protocol',
    'author': 'Lab Tech',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', 1
    )

    # Load pipette
    pipette = protocol.load_instrument(
        'p300_single_gen2', 'left'
    )

    # Your protocol steps here
    pipette.transfer(50, plate['A1'], plate['B1'])`}
        </pre>
      </div>
    </div>
  )
}
