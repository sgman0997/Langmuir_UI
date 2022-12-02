"""
balance callibrated by successive masses added
    masses converted to mN
    linear fit genreated from data set
    y = mx + b
    y = force mN
    m = raw (tared) balance value from serial input
    b = y intercept offset, should be close to 0 

force value on balance converted to mN
    raw balance value scaled according to linear fit formula
    
"""

# data set values
max_elements = 1500    # Maximum number of elements to display in plot, prevents excessive window refresh time
max_data = 50000       # max number of elements to store in any data set, prevents overflow and large data set accumulation

# wilhelmy plate values
# realistically- only the width needs to be updated as mass, length, and imersion_depth are unused, and thickness does not change much
p_mass = 34.4  # mg, was kg 
p_length = 20.00  # mm, was m
p_width = 12.54  # mm, was m
p_thickness = 0.00018 # mm, was m
imersion_depth = 1 # mm, was m
contact_angle = 0 # degrees


# subphase properties
sub_pahse_d = 0.001  # g/mm^3, was kg/m^3
pure_water_tension = 72.75  # mN/m at 20c
grav_acc = 9806.65 # mm/s^2


# trough properties, also set in trough calibration
trough_len_min = 74.00  # mm
trough_len_max = 217.74  # mm
trough_wid = 69.5  # mm
molecules = 1.3247E16  # molucules deposited
# moles = 2.1998E-8      # kept for record purposes

# calculated and constant properties
p_density = (p_mass/(p_length*p_width*p_thickness))
p_perimeter = 2 * (p_thickness + p_width)  # mm

# sub phase (water) density = 0.001 g/mm^3
# g/mm^3 * mm/s^2 * mm * mm * mm = g*mm/s^2 = uN = 0.001 mN
boyancy = sub_pahse_d * grav_acc * imersion_depth * p_thickness * p_width * 0.001 # mN
#print("boyancy: ", boyancy, "mN")
#print("perimeter: ", p_perimeter, "mm")
# callibration values
cal_num = 10           # number of input values needed to complete calibration
cal_time = 3           # seconds for scale to equalize before value is taken for calibration
mave = 20              # moving aveerage window
tare_num = 100         # number of samples to average when taring
compression_rate = 10  # Ang^2/molecule/minute




