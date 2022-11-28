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
max_elements = 2000    # Maximum number of elements to display in plot, prevents excessive window refresh time
max_data = 50000       # max number of elements to store in any data set, prevents overflow and large data set accumulation

# wilhelmy plate values
p_mass = 34.4  # mg, was kg 
p_length = 29.01  # mm, was m
p_width = 14.5  # mm, was m
p_thickness = 0.00018 # mm, was m
imersion_depth = 1 # mm, was m
contact_angle = 0 # degrees


# subphase properties
sub_pahse_d = 0.001  # g/mm^3, was kg/m^3
pure_water_tension = 72.75  # mN/m at 20c
grav_acc = 9806.65 # mm/s^2


# trough properties, also set in trough calibration
trough_len_min = 40  # mm
trough_len_max = 220  # mm
trough_wid = 70  # mm
molecules = 1.23E16  # molucules deposited

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
compression_rate = 100  # Ang^2/molecule/minute




