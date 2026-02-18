"""
Sample Protocol with Runtime Parameters
Demonstrates all parameter types for testing the parameter UI.
"""
from opentrons import protocol_api

requirements = {
    'robotType': 'OT-2',
    'apiLevel': '2.18'
}

metadata = {
    'protocolName': 'Runtime Parameters Demo',
    'author': 'Lab Technician',
    'description': 'Demonstrates runtime parameters for configurable protocols'
}


def add_parameters(parameters):
    parameters.add_int(
        display_name="Sample Count",
        variable_name="sample_count",
        default=8,
        minimum=1,
        maximum=96,
        description="Number of samples to process",
        unit="samples"
    )
    parameters.add_float(
        display_name="Transfer Volume",
        variable_name="transfer_volume",
        default=50.0,
        minimum=10.0,
        maximum=300.0,
        description="Volume to transfer per sample",
        unit="uL"
    )
    parameters.add_bool(
        display_name="Mix After Dispense",
        variable_name="mix_after",
        default=True,
        description="Whether to mix after dispensing"
    )
    parameters.add_str(
        display_name="Plate Type",
        variable_name="plate_type",
        default="biorad_96_wellplate_200ul_pcr",
        choices=[
            {"display_name": "Bio-Rad 96 PCR", "value": "biorad_96_wellplate_200ul_pcr"},
            {"display_name": "Corning 96 Flat", "value": "corning_96_wellplate_360ul_flat"},
            {"display_name": "NEST 96 Deep", "value": "nest_96_wellplate_2ml_deep"},
        ],
        description="Destination plate type"
    )
    parameters.add_int(
        display_name="Mix Repetitions",
        variable_name="mix_reps",
        default=3,
        choices=[
            {"display_name": "2 times", "value": 2},
            {"display_name": "3 times", "value": 3},
            {"display_name": "5 times", "value": 5},
            {"display_name": "10 times", "value": 10},
        ],
        description="Number of mix repetitions"
    )


def run(protocol: protocol_api.ProtocolContext):
    # Access runtime parameters
    sample_count = protocol.params.sample_count
    volume = protocol.params.transfer_volume
    mix_after = protocol.params.mix_after
    plate_type = protocol.params.plate_type
    mix_reps = protocol.params.mix_reps

    # Load labware
    dest_plate = protocol.load_labware(plate_type, 1, 'Destination Plate')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', 2, 'Reagent Reservoir')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 3, 'Tips 300uL')

    # Load pipette
    p300 = protocol.load_instrument(
        'p300_single_gen2', 'left', tip_racks=[tiprack]
    )

    # Transfer samples
    wells = dest_plate.wells()[:sample_count]

    for well in wells:
        p300.pick_up_tip()
        p300.aspirate(volume, reservoir['A1'])
        p300.dispense(volume, well)
        if mix_after:
            p300.mix(mix_reps, volume * 0.5, well)
        p300.drop_tip()

    protocol.comment(
        f"Done! Processed {sample_count} samples, "
        f"{volume} uL each, mix={'yes' if mix_after else 'no'}"
    )
