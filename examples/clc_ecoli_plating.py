metadata = {
    'protocolName': 'Ecoli Plating - CLC- TEST',
    'author': 'Lachlan <lajamu@biosustain.dtu.dk',
    'source': 'DTU Biosustain',
    'apiLevel': '2.11'
}

#TO DO: Switch to high vol first. Mix only on high vol. No spreading for high vol. 

import math
from opentrons import types


def run(protocol):
    def distribute_points_uniformly(total_radius, total_points, num_rings):
        points = []
        points.append((0, 0))  # Center point

        # Determine the total circumference to calculate the distribution of points
        total_circumference = sum(2 * math.pi * total_radius *
                                  (ring / num_rings)
                                  for ring in range(1, num_rings + 1))
        points_per_unit_length = total_points / total_circumference

        def add_points_on_ring(r, num_points):
            angle_increment = 360 / num_points
            for i in range(num_points):
                theta = degrees_to_radians(i * angle_increment)
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                points.append((x, y))

        for ring_number in range(1, num_rings + 1):
            ring_radius = total_radius * ring_number / num_rings
            ring_circumference = 2 * math.pi * ring_radius
            num_points = int(round(points_per_unit_length *
                                   ring_circumference))
            add_points_on_ring(ring_radius, max(num_points,
                                                1))  # Ensure at least 1 point

        return points

    # Helper function to convert degrees to radians
    def degrees_to_radians(degrees):
        return degrees * 3.141592653589793 / 180


# function to convert
#Load Tips1

    tips300 = [protocol.load_labware('opentrons_96_tiprack_300ul', '10')]
    p300 = protocol.load_instrument("p300_single", "right", tip_racks=tips300)

    tips20 = [protocol.load_labware('opentrons_96_tiprack_20ul', '11')]
    p20 = protocol.load_instrument("p20_single_gen2", "left", tip_racks=tips20)

    #Load plates
    plate_type = "corning_24_wellplate_3.4ml_flat"
    locs = [1]
    agarPlates_high = [
        protocol.load_labware(plate_type, slot, label="Agar Plates Low")
        for slot in locs
    ]

    locs2 = [2]
    agarPlates_low = [
        protocol.load_labware(plate_type, slot, label="Agar Plates High")
        for slot in locs2
    ]

    coli_dw = protocol.load_labware("usascientific_96_wellplate_2.4ml_deep", 9)

    rings_info = []

    points_on_well_high = distribute_points_uniformly(
        total_radius=(agarPlates_high[0]["A1"].diameter / 2) - 3,
        total_points=50,
        num_rings=4)

    points_on_well_low = distribute_points_uniformly(
        total_radius=(agarPlates_low[0]["A1"].diameter / 2) - 3,
        total_points=10,
        num_rings=4)

    def spot(pipette, dest, points, tot_plate_vol):
        """Takes a diluted transformed culture and spots the defined volume onto agar 
  in a Nunc omnitray"""
        spotting_dispense_rate = 0.25
        for point in points:
            pipette.move_to(dest.top().move(
                types.Point(x=point[0], y=point[1], z=10)))
            protocol.max_speeds["Z"] = 50
            pipette.move_to(dest.top().move(
                types.Point(x=point[0], y=point[1], z=2)))
            pipette.dispense(volume=tot_plate_vol / len(points),
                             rate=spotting_dispense_rate)
            pipette.move_to(dest.top().move(
                types.Point(x=point[0], y=point[1], z=0)))
            del protocol.max_speeds["Z"]

    def calculate_plate(w):
        p = w // 24
        return (p)

    def calculate_well(w):
        return (w % 24)

    def plate(w, vol_high, vol_low):
        p20.pick_up_tip()
        p20.mix(3, 20, coli_dw.wells()[w])
        p20.aspirate(vol_low, coli_dw.wells()[w])
        spot(p20,
             agarPlates_low[calculate_plate(w)].wells()[calculate_well(w)],
             points_on_well_low, vol_low)
        p20.drop_tip()
        p300.pick_up_tip()
        p300.mix(3, 50, coli_dw.wells()[w])
        p300.aspirate(vol_high, coli_dw.wells()[w])
        spot(p300,
             agarPlates_high[calculate_plate(w)].wells()[calculate_well(w)],
             points_on_well_high, vol_high)
        p300.drop_tip()

    high_vol = 90
    low_vol = 10

    for w in range(15):
        plate(w, high_vol, low_vol)
