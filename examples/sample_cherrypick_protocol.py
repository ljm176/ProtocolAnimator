"""
Sample Opentrons Protocol — CSV Cherrypicking
Demonstrates the csv_file runtime parameter for well-picking transfers.
Upload cherrypick_wells.csv alongside this protocol to test.
"""
from opentrons import protocol_api

metadata = {
    'protocolName': 'CSV Cherrypick Demo',
    'author': 'Lab Technician',
    'description': 'Transfer variable volumes between arbitrary wells using a CSV file'
}

requirements = {
    'robotType': 'OT-2',
    'apiLevel': '2.20'
}


def add_parameters(parameters):
    parameters.add_csv_file(
        display_name="Cherrypick Wells CSV",
        variable_name="cherrypick_wells",
        description="CSV with columns: source_slot, source_well, dest_slot, dest_well, volume"
    )
    parameters.add_bool(
        display_name="Dry Run",
        variable_name="dry_run",
        default=False,
        description="If enabled, skip actual liquid transfers and just move to wells"
    )
    parameters.add_float(
        display_name="Aspirate Speed Factor",
        variable_name="speed_factor",
        default=1.0,
        minimum=0.1,
        maximum=3.0,
        description="Multiplier for aspirate/dispense flow rates"
    )


def run(protocol: protocol_api.ProtocolContext):
    # Parse the CSV into rows
    csv_data = protocol.params.cherrypick_wells.parse_as_csv()
    dry_run = protocol.params.dry_run
    speed_factor = protocol.params.speed_factor

    # Load labware — slots referenced in the CSV
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 2, 'Source Plate')
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 3, 'Destination Plate')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 4, 'Tips 300uL')

    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Adjust flow rate
    pipette.flow_rate.aspirate *= speed_factor
    pipette.flow_rate.dispense *= speed_factor

    protocol.comment(f"Starting cherrypick: {len(csv_data) - 1} transfers, dry_run={dry_run}")

    # Process each row (skip header)
    for row in csv_data[1:]:
        source_slot, source_well, dest_slot, dest_well, volume = (
            row[0], row[1], row[2], row[3], float(row[4])
        )

        # Resolve labware by slot
        src_labware = source_plate if str(source_slot) == '2' else dest_plate
        dst_labware = dest_plate if str(dest_slot) == '3' else source_plate

        pipette.pick_up_tip()
        if dry_run:
            pipette.move_to(src_labware[source_well].top())
            pipette.move_to(dst_labware[dest_well].top())
            protocol.comment(f"[DRY RUN] Would transfer {volume} uL: {source_well} -> {dest_well}")
        else:
            pipette.aspirate(volume, src_labware[source_well])
            pipette.dispense(volume, dst_labware[dest_well])
            protocol.comment(f"Transferred {volume} uL: slot {source_slot} {source_well} -> slot {dest_slot} {dest_well}")
        pipette.drop_tip()

    protocol.comment("Cherrypick complete!")
