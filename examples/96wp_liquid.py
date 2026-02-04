import opentrons
from opentrons import protocol_api

metadata = {'apilevel' : '2.16',
            'protocolName': 'Coco - 96 well-plate liquid filing',
            'author': 'Jaime <jmutr@dtu.dk>'}

requirements = {"robotType": "OT-2", "apiLevel": "2.16"}


def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware('opentrons_96_tiprack_300uL', 11)
    reservoir = protocol.load_labware('nest_1_reservoir_195ml', 10)
    plates = [
    protocol.load_labware('corning_96_wellplate_360ul_flat', slot)
    for slot in range(1, 10)
    ]

    pip = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips])
    
    pip.pick_up_tip()
    for plate in plates:
        pip.distribute(100, reservoir['A1'], plate.rows()[0], new_tip='never')  
    pip.return_tip()