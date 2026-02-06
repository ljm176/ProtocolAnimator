nblocks = 15


metadata = {
    'protocolName': 'Transfer Blocks to 384',
    'author': 'Lachlan <lajamu@biosustain.dtu.dk',
    'source': 'DTU Biosustain',
    'apiLevel': '2.9'
}

def run(protocol):
    #tips300 = [protocol.load_labware("opentrons_96_tiprack_300ul", 1)]
    tips20 = [protocol.load_labware("opentrons_96_filtertiprack_20ul", 1)]
    #p300 = protocol.load_instrument('p300_single', 'right', tip_racks=tips300)
    p20 = protocol.load_instrument('p20_single_gen2', 'left', tip_racks = tips20)
    

    blockPlate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 2)
    echoPlate = protocol.load_labware("biorad_384_wellplate_50ul", 3)


    
    i = 0
    for i in range(nblocks):
      p20.pick_up_tip()
      for x in range(2):
        p20.transfer(20, blockPlate.wells()[i], echoPlate.wells()[i], new_tip = "never")
      i+=1
      p20.drop_tip()
    
