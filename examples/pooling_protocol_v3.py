"""
Pooling Protocol - Eppendorf 96-Well Plate to Tube Rack
Pool 2 uL from 32 wells (columns 2-5) and 20 uL from A1 and B5 into an eppendorf tube.
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'Pooling Protocol',
    'author': 'Lab Technician',
    'description': 'Pool 2 uL from columns 2-5 and 20 uL from A1/B5 into eppendorf tube',
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

    # Step 1: Pool 2 uL from 32 wells — B1 through A5, going down columns
    # Order: B1,C1...H1, A2,B2...H2, A3,B3...H3, A4,B4...H4, A5
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    pool_wells = []
    for col in range(1, 6):
        for row in rows:
            well = f'{row}{col}'
            if (col == 1 and row == 'A') or (col == 5 and row != 'A'):
                continue  # skip A1 (before start) and B5-H5 (after end)
            pool_wells.append(well)

    for well_name in pool_wells:
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

    # 32 x 2 uL + 2 x 20 uL = 104 uL total
    protocol.comment('Pooling complete! Total volume in tube A1: 104 uL')
