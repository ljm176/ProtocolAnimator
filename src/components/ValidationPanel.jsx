import { AlertCircle, CheckCircle, Info } from 'lucide-react'

export default function ValidationPanel() {
  const tips = [
    {
      title: 'Protocol Structure',
      description: 'Ensure your protocol has a run() function that accepts a ProtocolContext parameter',
    },
    {
      title: 'API Level',
      description: 'Specify the API level in metadata: {"apiLevel": "2.14"}',
    },
    {
      title: 'Import Statement',
      description: 'Use: from opentrons import protocol_api',
    },
    {
      title: 'Metadata',
      description: 'Include protocol name, author, and description in metadata dictionary',
      accent: true,
    }
  ]

  return (
    <div className="card p-6">
      <h2 className="font-mono text-sm font-medium text-text-secondary uppercase tracking-wider mb-5">
        Protocol Guidelines
      </h2>

      <div className="space-y-1">
        {tips.map((tip, idx) => (
          <div key={idx} className="flex gap-3 px-3 py-3 rounded-lg hover:bg-surface-2 transition-colors">
            <div className={`w-1 rounded-full flex-shrink-0 ${tip.accent ? 'bg-emerald-500' : 'bg-surface-4'}`} />
            <div>
              <h3 className="text-sm text-text-primary mb-0.5">{tip.title}</h3>
              <p className="text-xs text-text-tertiary leading-relaxed">{tip.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-surface-2 rounded-lg border border-edge">
        <h3 className="font-mono text-xs text-text-ghost uppercase tracking-wider mb-3">Example</h3>
        <pre className="text-xs text-text-tertiary p-3 bg-surface-0 rounded-lg border border-edge overflow-x-auto font-mono leading-relaxed">
{`from opentrons import protocol_api

metadata = {
    'protocolName': 'My Protocol',
    'author': 'Lab Tech',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware(
        'corning_96_wellplate_360ul_flat', 1
    )

    pipette = protocol.load_instrument(
        'p300_single_gen2', 'left'
    )

    pipette.transfer(50, plate['A1'], plate['B1'])`}
        </pre>
      </div>
    </div>
  )
}
