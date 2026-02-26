"""
Pooling Protocol - Eppendorf 96-Well Plate to Tube Rack
Pool 2 uL from wells A2-A5 and 20 uL from A1 and B5 into an eppendorf tube.
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'Pooling Protocol',
    'author': 'Lab Technician',
    'description': 'Pool 2 uL from A2-A5 and 20 uL from A1/B5 into eppendorf tube',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_20ul', 1, 'Tips 20uL')
    plate = protocol.load_labware('eppendorf_96_wellplate_500ul', 2, 'Eppendorf Plate')
    tube_rack = protocol.load_labware(
        'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 3, 'Tube Rack'
    )

    # Load pipette
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tiprack])

    # Destination: first tube in the rack
    dest = tube_rack['A1']

    # Step 1: Pool 2 uL from A2, A3, A4, A5 (columns 2-5, going down columns)
    pool_sources = ['A2', 'A3', 'A4', 'A5']
    for well_name in pool_sources:
        p20.pick_up_tip()
        p20.aspirate(2, plate[well_name])
        p20.dispense(2, dest)
        p20.drop_tip()

    # Step 2: Transfer 20 uL from A1 into tube
    p20.pick_up_tip()
    p20.aspirate(20, plate['A1'])
    p20.dispense(20, dest)
    p20.drop_tip()

    # Step 3: Transfer 20 uL from B5 into tube
    p20.pick_up_tip()
    p20.aspirate(20, plate['B5'])
    p20.dispense(20, dest)
    p20.drop_tip()

    protocol.comment('Pooling complete! Total volume in tube A1: 48 uL')
