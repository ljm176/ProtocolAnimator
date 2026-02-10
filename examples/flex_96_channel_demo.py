"""
Opentrons Flex Protocol - 96-Channel Pipette Demo
Simple liquid transfer using the 96-channel pipette
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'Flex 96-Channel Demo',
    'author': 'Lab Technician',
    'description': 'Transfer liquid from source to destination plate using 96-channel pipette'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.16'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load trash bin (required for Flex)
    trash = protocol.load_trash_bin('A3')

    # Load labware
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'D1', 'Source Plate')
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 'D2', 'Destination Plate')

    # Load tiprack on adapter (required for 96-channel full pickup)
    tiprack = protocol.load_labware(
        'opentrons_flex_96_tiprack_200ul',
        'A1',
        'Tips 200µL',
        adapter='opentrons_flex_96_tiprack_adapter'
    )

    # Load 96-channel pipette
    pipette_96 = protocol.load_instrument(
        'flex_96channel_1000',
        'left',
        tip_racks=[tiprack]
    )

    protocol.comment("Starting 96-channel transfer protocol")

    # Transfer 50 µL from source to destination (all 96 wells at once)
    pipette_96.pick_up_tip()

    # Aspirate from all 96 wells of source plate (A1 = all wells for 96-channel)
    pipette_96.aspirate(50, source_plate['A1'])
    protocol.comment("Aspirated 50 µL from all 96 wells of source plate")

    # Dispense to all 96 wells of destination plate
    pipette_96.dispense(50, dest_plate['A1'])
    protocol.comment("Dispensed 50 µL to all 96 wells of destination plate")

    # Mix the destination plate (3 times, 40 µL)
    pipette_96.mix(3, 40, dest_plate['A1'])
    protocol.comment("Mixed all 96 wells")

    # Drop tip
    pipette_96.drop_tip()

    protocol.comment("96-channel transfer complete!")
    protocol.comment("All 96 wells were processed simultaneously")
