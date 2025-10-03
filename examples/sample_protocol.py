"""
Sample Opentrons Protocol - PCR Preparation
This protocol demonstrates a simple PCR setup workflow
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'PCR Preparation',
    'author': 'Lab Technician',
    'description': 'Transfer samples and reagents for PCR setup',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    pcr_plate = protocol.load_labware('biorad_96_wellplate_200ul_pcr', 1, 'PCR Plate')
    reagent_plate = protocol.load_labware('nest_12_reservoir_15ml', 2, 'Reagent Reservoir')
    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 3, 'Tips 300µL')

    # Load temperature module (optional)
    temp_module = protocol.load_module('temperature module gen2', 4)
    sample_plate = temp_module.load_labware('biorad_96_wellplate_200ul_pcr', 'Sample Plate on Ice')

    # Set temperature module to 4°C
    temp_module.set_temperature(4)

    # Load pipette
    p300 = protocol.load_instrument(
        'p300_single_gen2',
        'left',
        tip_racks=[tiprack_1]
    )

    # Protocol steps
    # 1. Transfer master mix to all wells
    p300.pick_up_tip()
    for well in pcr_plate.wells()[:8]:  # First 8 wells
        p300.aspirate(50, reagent_plate['A1'])  # Master mix
        p300.dispense(50, well)
    p300.drop_tip()

    # 2. Transfer samples from cold plate
    for i, well in enumerate(pcr_plate.wells()[:8]):
        p300.pick_up_tip()
        p300.aspirate(10, sample_plate.wells()[i])
        p300.dispense(10, well)
        p300.mix(3, 30, well)  # Mix 3 times
        p300.drop_tip()

    # 3. Add water to control wells
    p300.pick_up_tip()
    for well in pcr_plate.wells()[8:12]:  # Control wells
        p300.aspirate(60, reagent_plate['A2'])  # Water
        p300.dispense(60, well)
    p300.drop_tip()

    protocol.comment("PCR setup complete!")
