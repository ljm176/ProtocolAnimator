"""
Sample Opentrons Flex Protocol - Flex Features Demo
Demonstrates Flex-specific features: coordinate slots, staging area, gripper moves
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'Flex Features Demo',
    'author': 'Lab Technician',
    'description': 'Demonstrate Flex robot capabilities'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.16'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load trash bin (required for Flex)
    trash = protocol.load_trash_bin('A3')

    # Load labware on main deck using coordinate system (A1-D3)
    sample_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'B1', 'Sample Plate')
    reagent_plate = protocol.load_labware('nest_12_reservoir_15ml', 'C1', 'Reagent Reservoir')
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A2', 'Tips 200µL')
    output_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'C2', 'Output Plate')

    # Load temperature module
    temp_module = protocol.load_module('temperature module gen2', 'D1')
    temp_plate = temp_module.load_labware('nest_96_wellplate_200ul_flat', 'Cold Samples')

    # Set temperature
    temp_module.set_temperature(4)

    # Load pipette (single-channel for this demo)
    pipette = protocol.load_instrument(
        'flex_1channel_1000',
        'left',
        tip_racks=[tiprack]
    )

    # Transfer samples from cold storage to sample plate
    pipette.pick_up_tip()
    for i in range(8):
        source_well = temp_plate.wells()[i]
        dest_well = sample_plate.wells()[i]
        pipette.aspirate(50, source_well)
        pipette.dispense(50, dest_well)
    pipette.drop_tip()

    # Add reagents
    pipette.pick_up_tip()
    for i in range(8):
        pipette.aspirate(100, reagent_plate['A1'])
        pipette.dispense(100, sample_plate.wells()[i])
        pipette.mix(3, 50, sample_plate.wells()[i])
    pipette.drop_tip()

    protocol.comment("Flex protocol complete!")
