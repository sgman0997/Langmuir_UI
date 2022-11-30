"""
TODO list-------------------------------------


allow for isotherm run interrupt
verify pressure/tension relationship in Sample()
    

nice to haves--------------------------------
impliment pandas for data sets
pause main animate loop when running isotherm
on shutdown, save last slope, intercept, and tare offsets for next startup config
check load cell 2 periodically for changes in environment
dump data sets on overflow


notable issues------------------------------
input buffer accumulates constantly and must be cleared before most recent values are obtained.
    this does not appear to impact performance that much, but is not ideal

"""
import RPi.GPIO as GPIO
import tkinter as tk
import tkinter.font as tkFont
import time
import serial
import matplotlib.figure as figure
import matplotlib.animation as animation
import matplotlib.dates as mdates
import numpy as np
import csv
import scipy
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from lang_config import *
from scipy import stats  # verify
#from linear_regression import linear_regression

###############################################################################
#stepper motor GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# coil numbers corrospond to Pi vertual GPIO pin numbers 
coil_B_1_pin = 6  # pi 31, ULN2003 in 1
coil_A_1_pin = 13 # pi 33, ULN2003 in 2
coil_B_2_pin = 19 # pi 35, ULN2003 in 3
coil_A_2_pin = 26 # pi 37, ULN2003 in 4
# stepper motor parameters, adjust if different motor used
StepCount=8
Seq = [[0,1,0,0],[0,1,0,1],[0,0,0,1],[1,0,0,1],[1,0,0,0],[1,0,1,0],[0,0,1,0],[0,1,1,0]]
GPIO.setup(coil_A_1_pin, GPIO.OUT)
GPIO.setup(coil_A_2_pin, GPIO.OUT)
GPIO.setup(coil_B_1_pin, GPIO.OUT)
GPIO.setup(coil_B_2_pin, GPIO.OUT)
# trough variables, square angstroms used for lit consistency
# many of these values are default estimates.  barrier_pos, trough_closed_ang, trough_open_ang, area_per_step, working_area_ang
area_per_step = 689936400000000.1    # will be area change for each step of barrier motor, Ang^2
barrier_pos = 0                      # will be position of barrier in stepper motor steps, expected to start open at 0
area_per_mol = 100                   # will be calculated based on moles deposited and trough area, Ang^2
trough_closed_ang = 1.9364076000000003e+17         # ang^2, surface area when trough fully closed
trough_open_ang = 1.5735135600000003e+18         # ang^2, surface area when trough fully open
current_area_ang = 1.5735135600000003e+18        # ang^2, activly updated value representing current trough surface area
barrier_closed = 2000                # barrier pos at fully closed, fully open = 0
##############################################################

# animation and balance parameters
animation_interval = 200 # Time (ms) between animation updates, impacts sample normal rate, but not run sample rate

# calibration and tare variables
slope = -1.4301602559451846e-05    # linear fit slope for scaling raw balance values, updated in Calibration
intercept = 0                      # linear fit intercept for shifting raw balance values, updated in Calibration
slope2 = slope                     # 2nd balance not calibrated, balance value for qualitative comparison only
intercept2 = 0                     # 2nd balance not calibrated, balance value for qualitative comparison only
tare_offset1 = 0                   # value by which to shift raw arduino value (hx711) read from dev/ttyACM0
tare_offset2 = 0                   # 2nd balance tare offset

# isotherm run values
isotherm_speed = 1         # will be speed at which barriers are closed for isotherm
isotherm_area_initial = 1  # set before each barrier movement
isotherm_area_final = 1    # set to control distance of barrier movement

root = None
dfont = None
frame = None
canvas = None
ax1 = None
fullscreen = False

# data sets
dt = mdates.date2num(datetime.now())
sample_data = []
pressure_data = []
tension_data = []
cell2_data = []
sample_timestamps = []
sample_data_ave1 = []
sample_data_ave2 = []
force1_data = []
sample_fields = ['area_per_mol', 'surface_pressure',
                        'sdt', 'barrier_pos', 'cell2_value', 
                        'force_value', 'surface_tension', 'current_area_ang',
                        'mave1', 'mave2', 'tare_offset1, tare_offset2']
#cal_vals_x = [0] * cal_num   # list of calibration values
 
# data display choices
disp_pressure = True
disp_force = False
disp_mave = False
disp_cell2 = False

# begin serial connection
ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)
ser.reset_input_buffer()

###############################################################################
# Functions

# Toggle fullscreen
def toggle_fullscreen(event=None):
    global root
    global fullscreen
    fullscreen = not fullscreen
    root.attributes('-fullscreen', fullscreen)
    resize(None)   

# Return to windowed mode
def end_fullscreen(event=None):
    global root
    global fullscreen
    fullscreen = False
    root.attributes('-fullscreen', False)
    resize(None)

# Automatically resize font size based on window size
def resize(event=None):
    global dfont
    global frame
    # Resize font based on frame height (minimum size of 12)
    # Use negative number for "pixels" instead of "points"
    new_size = -max(12, int((frame.winfo_height() / 15)))
    dfont.configure(size=new_size)


# This function is called periodically from FuncAnimation and is the main loop function
def animate(i, ax1, cell_val, barrier_pos_an):
    # a sample is taken every time the animation is refreshed
    # this is not ideal, but does not impact the isotherm since isotherm samples are taken much more slowly
    # display options
    global disp_pressure
    global disp_force
    global disp_mave
    global disp_cell2
    # data sets
    global tension_data
    global pressure_data
    global cell2_data
    global sample_timestamps
    global sample_data_ave1
    global sample_data_ave2
    global force1_data
    
    global barrier_pos
    
    Sample()  # calls the sample function which appends a single sample value to all data sets
    barrier_pos_an.set(barrier_pos)
    # check data set for display, sets the single display value
    # Clear, format, and plot cell values first (behind)
    # redraws plot each time animate is called
    # resource intensive, would be nice to find a better method
    if disp_force:  # load cell 1 converted to tension
        cell_val.set(round(force1_data[-1],3))
        color = 'tab:blue'
        ax1.clear()
        ax1.set_ylabel('Force on balance (mN)', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        x_set = sample_timestamps[-max_elements:]
        y_set = force1_data[-max_elements:]
        ax1.plot(x_set, y_set, linewidth=2, color=color)
    elif disp_pressure:  # load cell 1 converted to pressure
        cell_val.set(round(pressure_data[-1],3))
        color = 'tab:red'
        ax1.clear()
        ax1.set_ylabel('Monolayer Surface Pressure (mN/m)', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        x_set = sample_timestamps[-max_elements:]
        y_set = pressure_data[-max_elements:]
        ax1.plot(x_set, y_set, linewidth=2, color=color)
    elif disp_mave:  # load cell 2 force simple moving average
        cell_val.set(round(sample_data_ave2[-1],3))
        color = 'tab:green'
        ax1.clear()
        ax1.set_ylabel('Cell 2 force: simple moving average (mN)', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        x_set = sample_timestamps[-max_elements:]
        y_set = sample_data_ave2[-max_elements:]
        ax1.plot(x_set, y_set, linewidth=2, color=color)
    else:  # load cell 2 raw force val
        cell_val.set(round(cell2_data[-1],3))
        color = 'tab:purple'
        ax1.clear()
        ax1.set_ylabel('Load cell 2 approxiate force value (mN)', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        x_set = sample_timestamps[-max_elements:]
        y_set = cell2_data[-max_elements:]
        ax1.plot(x_set, y_set, linewidth=2, color=color)
    # Format timestamps to be more readable
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.set_xlabel('sample time stamps')
    fig.autofmt_xdate()


# generates raw data to be used by cal, tare, sample...
def Raw():
    ser.reset_input_buffer()  # clean up input puffer to make most recent value available
    success = 0
    while not success: #must get a valid value to continue
        # TODO may be necessary to include a timeout here eventually to catch errors
        ser.reset_input_buffer()
        while ser.in_waiting < 16: # wait for enough serial data
            pass
        line = ser.readline()  # output from arduino
        line = line.decode("utf-8").strip().split()  
        if len(line) == 3:  # if less than 3, data was lost in transit
            sr1 = float(line[1])  # [0] = "line:" and helps identify lost data
            sr2 = float(line[2])  # raw hx711 value, 0 to 16777215
            sdt = mdates.date2num(datetime.now())
            success = 1
    #print(sdt, sr1, sr2)
    return sr1, sr2, sdt


"""
the math done in this method is explained in depth in the thesis paper writted for this project.
see equasions 1-7 in section 2.1.1

"""
def Sample():
    global sample_data  # all, raw
    global tension_data
    global pressure_data
    global cell2_data
    global sample_timestamps
    global sample_data_ave1
    global sample_data_ave2
    global force1_data
    
    global tare_offset1
    global tare_offset2
    global slope
    global slope2
    global intercept
    global intercept2
    global current_area_ang
    global barrier_pos
    global area_per_mol
    
    sr1, sr2, sdt = Raw()  # raw sample data unmodified by tare offset or linear fit value
    # force value (mN) = (raw sensor value - tare offset) * slope + intercept
    force_value = (sr1 - tare_offset1) * slope  # + intercept  # slope scales value to mN, intercept included so linear region more accurate
    # surface tension and surface pressure values should remain in mN/m to be consistant with literature
    # surface tension should be 72.75 (at 20C) when plate immersed, tared, and no lipid present
    force_per_meter = force_value/(p_perimeter*0.001)  # perimeter converted to m to keep mN/m consistancy
    surface_tension = pure_water_tension + force_per_meter  # Eq. 6 from Scott Gere thesis paper
    # surface pressure should be 0 when tared and no lipid deposited
    surface_pressure = -force_per_meter  # Eq. 7 from Scott Gere thesis paper
    
    # tension and pressure values for balance #2 are given as if balance 2 were used, though it is not
    force_value2 = (sr2 - tare_offset2) * slope2 #+ intercept  #  not valid unless scale 2 has been callibrated
    # not necessary since balance 2 is not used to suspend a plate
    #force_per_meter2 = force_value2/(p_perimeter*0.001)
    #surface_tension2 = pure_water_tension + force_per_meter2
    #surface_pressure2 = -force_per_meter2
    
    cell2_value = force_value2
    
    # clean data
    force1_data.append(force_value)
    sample_timestamps.append(sdt)  # time stamp
    tension_data.append(surface_tension) 
    pressure_data.append(surface_pressure)  # 
    cell2_data.append(cell2_value)
    #print(sdt, sr1, sr2)  # shell output for development
    
    mave1 = np.average(tension_data[-mave:])
    mave2 = np.average(cell2_data[-mave:])
    sample_data_ave1.append(mave1)
    sample_data_ave2.append(mave2)
    
    # all data set values, good for dumping post experiment
    sample_data.append([area_per_mol, surface_pressure,
                        sdt, barrier_pos, cell2_value, 
                        force_value, surface_tension, current_area_ang,
                        mave1, mave2, tare_offset1, tare_offset2]) 
    return force_value, surface_tension, surface_pressure, sdt
    

def Tare():
    # bring in data sets
    global pressure_data
    global tension_data
    global cell2_data
    global force1_data
    global sample_timestamps
    global sample_data_ave1
    global sample_data_ave2
    global tare_offset1  # raw offset value for balance zero
    global tare_offset2
    #tare_pop = Disp_message("Taring")
    tare_data1 = []
    tare_data2 = []
    for i in range(tare_num):  # sample ran for tare_num times
        sr1, sr2, sdt = Raw() 
        tare_data1.append(sr1)  # save tare values
        tare_data2.append(sr2)
    
    tare_offset1 = np.average(tare_data1)
    tare_offset2 = np.average(tare_data2)
    print("raw balance values tared at: ", tare_offset1, tare_offset2)
    # clear data sets after offset value obtained
    pressure_data = []
    tension_data = []
    cell2_data = []
    sample_timestamps = []
    sample_data_ave1 = []
    sample_data_ave2 = []
    force1_data = []


"""
balance callibration results in slope and intercept values that will be used to modify the raw sensor value
to reflect milli newtons of force on the balance. this is based on adding known masses to the balance.
masses added must be in grams currently.

1ml water = 1gm, 50ul = 0.05gm, repeatedly adding 50ul of water to balnace is a good calibration method
"""
def Calibrate_balance():
    global cal_num  # number of cal samples to take, more = better linerar fit
    global cal_time  # settle time in seconds for each sample, more = longer settle time
    global slope
    global intercept
    global tare_offset1
    global tare_num
    #print(tare_num, tare_offset1, slope, intercept)
    Tare()  # raw hx711 output value tared (shifted to 0). no scaling applied to tare offset
    time.sleep(cal_time)  # allow balance to settle
    
    mass_sum = 0  # accumulate successive mass values added to balance
    cal_vals_x = [tare_offset1]  # initialize x and y data sets for linear fit
    cal_vals_y = [0]  # starting point, current balance raw value just after tare
    cal_vals = [[tare_offset1, 0]]  # for saving to file 
    # use raw values for data set
    for i in range(cal_num):  # number of callibration points for linear fit
        mass_added = float(askstring("Mass Input", "add mass to balance, input mass added in grams, and wait for next calibration step"))
        # TODO consider a wait message here, destroy message after sleep time over
        
        #time.sleep(cal_time)  # wait for values to accumulate
        # simple moving average (mave) based on tare num for each data point
        cal_data1 = []  # fresh data set for mave
        for i in range(tare_num):  # sample ran for tare_num times
            sr1, sr2, sdt = Raw() 
            cal_data1.append(sr1)  # save cal value only for call 1
        
        scale_val = np.average(cal_data1)  # next ave scale value for data point
        mass_sum += mass_added  # cululative mass added for force calculation
        # convert input mass to milli newtons
        force = mass_sum * 9.81  # g * m/s^2 = mN, milli newtons
        cal_vals_x.append(scale_val)  # average of raw scale value
        cal_vals_y.append(force)   # total force applied to scale
        cal_vals.append([scale_val, force])
        # continue loop 
    #print(cal_vals_x)
    #print(cal_vals_y)
    # generate line function
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(cal_vals_x, cal_vals_y)
    r_squared = r_value**2
    #slope_intercept = np.polyfit(cal_vals_x, cal_vals_y, 1)  # fit based on mN
    #slope, intercept = linear_regression(cal_vals_x, cal_vals_y, proportional=True)
    #slope = float(slope_intercept[0])  # scales sensor value to force (mN)
    #intercept = float(slope_intercept[1])  # shifts sensor value to force (mN) intercept
    message  = "slope: " + repr(slope) + " intercept: " + repr(intercept)
    params = [["slope: ", repr(slope)], ["intercept: ", repr(intercept)],
              ["r_value: ", r_value], ["r_squared: ", r_squared], ["p_value: ", p_value], ["std_err: ", std_err],
              ["cal_num: ", cal_num], ["cal_time: ", cal_time]]
    showinfo("slope and intercept", message)
    print(slope, intercept, r_value, p_value, std_err, r_squared)
    Save_data(cal_vals, ['scale values', 'force values'], 'last_balance_cal.txt', params)


def Contam_check():
    #global barrier_pos
    Open_full()
    showinfo("Contamination Check", "Make sure plate is immursed 1 mm below subphase surface")
    Tare()
    force_value, surface_tension, surface_pressure, sdt = Sample()
    Close_full()
    force_value2, surface_tension2, surface_pressure2, sdt2 = Sample()
    force_diff = force_value - force_value2
    tension_diff = surface_tension - surface_tension2
    pressure_diff = surface_pressure - surface_pressure2
    message = f"force_diff:{force_diff}, tension_diff:{tension_diff}, pressure_diff:{pressure_diff}"
    showinfo("Contamination Check", message)
    Open_full()
    

def Get_val_window(): # top
    top = Toplevel(root)
    top.geometry("750x250")
    entry = Entry(top, width=25)
    entry.pack()
    Button(top, text="Input first mass", command=lambda:Insert_vals(entry)).pack(pady=5, side=TOP)
    Button(top, text="Finish", command=lambda:Close_pop(top)).pack(pady=5, side=TOP)
    #prompt user for wilhelmy plate parameters, lipid details, sampling ave size, barrier speed 
    pass


# currently not used, may impliment if time permits
def Disp_message(message): # be sure to call Close_pop
    pop = Toplevel(root)
    pop.geometry("750x250")
    Label(pop, text=message).pack(pady=5, side=TOP)
    #Label(top, text="Input first mass", command=lambda:Insert_vals(entry))
    #Button(top, text="Finish", command=lambda:Close_setup(top)).pack(pady=5, side=TOP)
    #prompt user for wilhelmy plate parameters, lipid details, sampling ave size, barrier speed 
    print("popup generated")
    return pop  # necessary to close pop


def Close_pop(pop):
    pop.destroy()
    print("popup destroyed")


def Insert_vals(v1):
    v1.insert(0, 'test1')
    #v2.insert(0, 'test2')

"""
main isotherm run function
generates multiple data sets
moves barriers, takes sample after each move
saves data sets to csv when isotherm complete
"""
def Run():
    global barrier_pos   # current abs position of the barrier in motor steps, full open = 0
    global barrier_closed  # fully closed step pos
    global area_per_mol  # calculated actively druring barrier movement
    global area_per_step  # 
    global trough_open_ang  # 
    global compression_rate  # Ang^2/molecule/min, desired rate of compression
    global molecules  # set in config
    global mave  # set in config
    sample_num = barrier_closed - barrier_pos  # number of step/sample actions to take, default = remaining steps to close
    
    # removed, rate not currently used, increase smoothing to slow down isotherm
    #try:
    #    area_rate = float(askstring("Run values, cancel for default", "Input desired sample rate (Ang^2/Molecule/min), 10 is normal."))
    #except TypeError:
    #    area_rate = compression_rate # else default compression_rate
    try:
        moles_in = float(askstring("Run values, cancel for default", "Input Moles of lipid deposited."))
        molecules = moles_in * 6.02214E23
    except TypeError:
        moles_in =  "default value" # else default molecules
    try:
        smoothing = int(askstring("Run values, cancel for default", "Input sample smoothing size. 4 is normal"))
    except TypeError:
        smoothing = mave  # else default mave
    try:
        sample_steps = int(askstring("Run values, cancel for default", "Input barrier steps. negative values will give expansion isotherm"))
    except TypeError:
        sample_steps = sample_num # else default sample_num
    """
    this is not that necessary. the idea was to build the stepper motor delay
    based on the desired isotherm sampling rate. these rates are important to langmuir isotherms
    and are cited in literature. the difficulty here is that the Raw() function, and as a result th Sample() function,
    has a non-negligible impact on the time it takes to measure a single data point.
    tests so far have concluded that a single sample call takes a little more than 1 second to complete currently
    therefore, a 2000 point sample with 10 points of moving average for each sample will take over 5.5 hours without
    including the stepper delay. This could be a good thing for some Isotherm experiments, but makes it difficult
    to perform experiments at faster sampling rates.
    """
    area_change_expected = sample_steps * area_per_step
    #t_seconds  = ((area_change_expected / compression_rate) / molecules) * 60
    #sec_per_step = t_seconds / sample_steps
    #delay = sec_per_step
    delay = 0.001
    #print(area_change_expected, t_seconds, sec_per_step)
    iso_data = []  # isotherm data callection to be saved in csv
    iso_data_long = []
    # initial sample to initialize variables
    force_value, surface_tension, surface_pressure, sdt = Sample()
    sample_start = mdates.num2date(sdt)
    iso_type = ""
    if sample_steps > 0:
        iso_type = "Compression"
        # make sure steps dont exceed available range
        avail_range = barrier_closed - barrier_pos
        if sample_steps > (avail_range):
            sample_steps = avail_range
        for i in range(sample_steps):  # number of step/sample actions to take
            Close_trough(delay, 1)  # single barrier step
            sample_data = []  # fresh data set for mave
            for j in range(smoothing):  # samples taken for mave
                force_value, surface_tension, surface_pressure, sdt = Sample()
                sample_data.append(surface_pressure)
                #print("tp2", smoothing, i, surface_pressure, barrier_pos, sdt)
            press_val = np.average(sample_data)  # next ave pressure value for data point
            iso_data.append([area_per_mol, press_val])
            print("compression values: ", i, area_per_mol, press_val, barrier_pos, sample_steps, smoothing, moles_in, molecules, compression_rate)
            iso_data_long.append([barrier_pos, area_per_mol, press_val, surface_pressure, surface_tension, sdt])
    else:
        iso_type = "Expansion"
        # make sure steps dont exceed available range
        if abs(sample_steps) > (barrier_pos):
            sample_steps = -barrier_pos
        for i in range(abs(sample_steps)):  # number of step/sample actions to take
            Open_trough(delay, 1)  # single barrier step
            sample_data = []  # fresh data set for mave
            for j in range(smoothing):  # samples taken for mave
                force_value, surface_tension, surface_pressure, sdt = Sample()
                sample_data.append(surface_pressure)
                #print("tp2", smoothing, i, surface_pressure, barrier_pos, sdt)
            press_val = np.average(sample_data)  # next ave pressure value for data point
            iso_data.append([area_per_mol, press_val])
            print("expansion values: ", i, area_per_mol, press_val, barrier_pos, sample_steps, smoothing, moles_in, molecules, compression_rate)
            iso_data_long.append([barrier_pos, area_per_mol, press_val, surface_pressure, surface_tension, sdt])

    sample_end = mdates.num2date(sdt)
    iso_params = [["start time: ", sample_start], ["end time: ", sample_end], ["number of smooting values: ", smoothing],
                  ["total sample steps: ", sample_steps], ["stepper delay: ", delay],
                  ["area_change_expected: ", area_change_expected], ["molecules deposited: ", molecules],
                  ["plate perimeter: ", p_perimeter], ["plate width: ", p_width],
                  ["isotherm type: ", iso_type]] 
    f_name = "Isotherm_" + str(sdt) + ".txt"
    Save_data(iso_data, ['area_per_molecule (Ang^2/molecule)', 'surface pressure (mN/m)'], f_name, iso_params)
    Save_data(iso_data_long, ['barrier_pos', 'area_per_mol',
                              'press_val', 'surface_pressure', 'surface_tension', 'sdt'], "run_backup.txt", iso_params)
    

def Get_file_name():
    file_name = askstring("File name input", "input file name and extension")
    return file_name


# save data to csv file
def Save_data(sample_data=sample_data, sample_fields=sample_fields, f_name=False, iso_params=False):
    if not f_name:
        f_name = Get_file_name()  # choose file to dump to, prevents unintentional overwrite
    f_name = "Data_files/" + f_name
    with open(f_name, 'w') as file:
        write = csv.writer(file)
        if iso_params:
            write.writerow(["----isotherm parameters----"])
            write.writerows(iso_params)
            write.writerow(["----isotherm data----"])
        write.writerow(sample_fields)
        write.writerows(sample_data)
    

def setStep(w1, w2, w3, w4):
    GPIO.output(coil_A_1_pin, w1)
    GPIO.output(coil_A_2_pin, w2)
    GPIO.output(coil_B_1_pin, w3)
    GPIO.output(coil_B_2_pin, w4)


"""
To callibrate trough,
    move barrier full open. This will set full open to zero.
    measure and record fully open trough length for later input
    then move barrier full closed, this will set barrier pos to max value
    measure and record fully closed length for later input
    then push calibrate trough button
    input recorded values
display input values message 
    distance traveled calulated from inputs
    current trough area calculated
    area per step calculated
"""
def Calibrate_trough():
    # currently: barrier pos set prior to calibration
    # ideally: user would be prompted to move barrier and then given time to measure
    #     this may be possible, but would require blicking root and still allowing barrier movement
    global barrier_pos  # abs position of the barrier in motor steps, full open = 0
    global barrier_closed  # barrier pos at fully closed, fully open = 0
    global trough_len_min  # mm
    global trough_len_max  # mm
    global trough_wid  # mm
    global molecules
    global trough_closed_ang  # ang^2
    global trough_open_ang  # ang^2
    global area_per_step    # area change for each step of barrier motor, Ang^2, set here
    
    global current_area_ang  # ang^2, set here
        
    trough_len_max = float(askstring("Calibrate Trough",
                         "Input length of open trough in mm"))
    cal_steps = int(askstring("Calibrate Trough",
                         "Input steps to open by, 2000 is normal"))
    Close_trough(0.001, cal_steps)
    trough_len_min = float(askstring("Calibrate Trough",
                         "Input length of closed trough in mm"))
    barrier_dist = trough_len_max - trough_len_min
    trough_area_open = trough_wid * trough_len_max  # mm^2
    trough_area_closed = trough_wid * trough_len_min  # mm^2
    barrier_closed = barrier_pos  # store closed barrier pos
    
    trough_open_ang = trough_area_open * 1E14  # ang^2
    trough_closed_ang = trough_area_closed * 1E14  # ang^2
    working_area_ang = trough_open_ang - trough_closed_ang
    area_per_step = working_area_ang/barrier_pos  # ang^2/step
    print(barrier_pos, trough_closed_ang, trough_open_ang, area_per_step, working_area_ang)
    Open_full()  # open barrier after trough cal to prepare for tests
    current_area_ang = trough_open_ang  # set current area angstoms based on open position
    print(current_area_ang, trough_len_min, trough_len_max)
    #TODO
    #Save_data(cal_vals, ['scale values', 'force values'], 'last_trough_cal.txt', slope_intercept)
    

"""
main trough area and barrier position update method
called every time barrier is moved one step open or closed
"""
def Barrier_update(direction=1):  # -1 = close, 1 = open
    global barrier_pos  # abs position of the barrier in motor steps, full open = 0
    global StepCount
    global current_area_ang  # actively updated here
    global area_per_mol  # actively updated here, calculated based on moles deposited and current trough area, Ang^2
    global area_per_step  # area change per motor step, calculated during trough calibration
    global molecules  # molecules of lipid deposited
    
    if direction == 1:  # opening, pos down, area up, full open = 0
        barrier_pos -= 1
        current_area_ang += area_per_step  # Ang^2
    else:  # closing, pos up, area down
        barrier_pos += 1
        current_area_ang -= area_per_step  # Ang^2
    area_per_mol = current_area_ang/molecules  # update area per molecule
    if barrier_pos < 0:  # fully open becomes new baseline
        barrier_pos = 0

def Open_trough(delay=0.01, steps=10):
    global StepCount  
    for i in range(steps):
        Barrier_update(1)
        for j in range(StepCount):
            # one step taken
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)
        
        
def Close_trough(delay=0.01, steps=10):
    global StepCount
    for i in range(steps):
        Barrier_update(-1)
        for j in reversed(range(StepCount)):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)

# called by tk buttons, there is probably a better way to do this
def Close_trough2(delay=0.001):
    steps = int(askstring("Close steps",
                         "Input number of steps to close by"))
    Close_trough(delay, steps)
    
    
def Open_trough2(delay=0.001):
    steps = int(askstring("Open steps",
                         "Input number of steps to open by"))
    Open_trough(delay, steps)
    
def Close_full(delay=0.001):
    global barrier_pos  # current barrier pos in steps
    global barrier_closed  # fully closed barrier pos, max steps
    steps = barrier_closed - barrier_pos  # remaining steps needed to close
    Close_trough(delay, steps)
    
def Open_full(delay=0.001):
    global barrier_pos
    steps = barrier_pos
    Open_trough(delay, steps)  # fully open = 0, current pos = remain steps needed to open

def toggle_cell():
    global disp_pressure
    global disp_force
    global disp_mave
    global disp_cell2
    if disp_pressure:  # if press true, set false and shift to tension
        disp_pressure = not disp_pressure
        disp_force = not disp_force
    elif disp_force:  # if tension true, set false and shift to mave
        disp_force = not disp_force
        disp_mave = not disp_mave
    elif disp_mave:  # if mave true, set false and shift to cell2
        disp_mave = not disp_mave
        disp_cell2 = not disp_cell2
    else:  # if cell2 true, reset the values to starting values
        disp_pressure = True
        disp_force = False
        disp_mave = False
        disp_cell2 = False
    
    
def combine_cells():
    pass


# Dummy function prevents segfault
def _destroy(event):
    pass

###############################################################################
# Main script

# Create the main window
root = tk.Tk()
root.title("Langmuir APP")

# Create the main container
frame = tk.Frame(root)
frame.configure(bg='white')

# Lay out the main container (expand to fit window)
frame.pack(fill=tk.BOTH, expand=1)

# Create figure for plotting
fig = figure.Figure(figsize=(2, 2))
fig.subplots_adjust(left=0.1, right=0.8)
ax1 = fig.add_subplot(1, 1, 1)

# Instantiate a new set of axes that shares the same x-axis
#ax2 = ax1.twinx()

# Variables for holding cell data
cell_val = tk.IntVar()
barrier_pos_an = tk.IntVar()  # animated barrier pos

# Create dynamic font for text
dfont = tkFont.Font(size=-10)

# Create a Tk Canvas widget out of our figure
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_plot = canvas.get_tk_widget()

# Create other supporting widgets
#pass in data set label if time permits
#label_cell_name = tk.Label(frame, text=cell_label, font=dfont, bg='white')
label_cell_name = tk.Label(frame, text='Y axis value: ', font=dfont, bg='white')
label_cell = tk.Label(frame, textvariable=cell_val, font=dfont, bg='white')
label_barrier = tk.Label(frame, text='Barrier pos: ', font=dfont, bg='white')
label_barrier_pos = tk.Label(frame, textvariable=barrier_pos_an, font=dfont, bg='white')


button_tare = tk.Button(    frame,
                            text="Tare balance",
                            font=dfont,
                            command=Tare)
button_toggle = tk.Button(    frame,
                            text="Toggle data",
                            font=dfont,
                            command=toggle_cell)
button_run = tk.Button(    frame,
                            text="Run Isotherm",
                            font=dfont,
                            command=Run)
button_contam_check = tk.Button(    frame,
                            text="Contam. Check",
                            font=dfont,
                            command=Contam_check)
button_cal = tk.Button(    frame, # popup calibration window for balance
                            text="Cal balance",
                            font=dfont,
                            command=Calibrate_balance)
button_cal_trough = tk.Button(    frame, # popup calibration window for trough
                            text="Cal trough",
                            font=dfont,
                            command=Calibrate_trough)
button_close_trough = tk.Button(    frame,
                            text="<-",
                            font=dfont,
                            command=Close_trough)
button_open_trough = tk.Button(    frame,
                            text="->",
                            font=dfont,
                            command=Open_trough)
button_close2_trough = tk.Button(    frame,
                            text="<<-",
                            font=dfont,
                            command=Close_trough2)
button_open2_trough = tk.Button(    frame,
                            text="->>",
                            font=dfont,
                            command=Open_trough2)
button_save = tk.Button(    frame,
                            text="Save data",
                            font=dfont,
                            command=Save_data)
button_quit = tk.Button(    frame,
                            text="Quit",
                            font=dfont,
                            command=root.destroy)

# Lay out widgets in a grid in the frame
canvas_plot.grid(   row=0, 
                    column=0, 
                    rowspan=6, 
                    columnspan=7, 
                    sticky=tk.W+tk.E+tk.N+tk.S)

# barrier move buttons
button_close2_trough.grid(row=6, column=0, sticky=tk.W)
button_close_trough.grid(row=6, column=1, sticky=tk.W)
button_open_trough.grid(row=6, column=2, sticky=tk.W)
button_open2_trough.grid(row=6, column=3, sticky=tk.W)

# column 0
label_cell_name.grid(row=0, column=0, sticky=tk.N)

# column 1
label_cell.grid(row=0, column=1, sticky=tk.N)

# column 2
label_barrier.grid(row=0, column=2, sticky=tk.N)

# column 3
label_barrier_pos.grid(row=0, column=3, sticky=tk.N)

# column 4
#label_unit.grid(row=6, column=4, sticky=tk.W)
button_contam_check.grid(row=6, column=4, columnspan=2)

# column 6
button_cal.grid(row=0, column=6, columnspan=2)
button_cal_trough.grid(row=1, column=6, columnspan=2)
button_tare.grid(row=2, column=6, columnspan=2)
button_toggle.grid(row=3, column=6, columnspan=2)
button_run.grid(row=4, column=6, columnspan=2)
button_save.grid(row=5, column=6, columnspan=2)
button_quit.grid(row=6, column=6, columnspan=2)



# Add a standard 5 pixel padding to all widgets
for w in frame.winfo_children():
    w.grid(padx=5, pady=5)

# Make it so that the grid cells expand out to fill window
for i in range(0, 5):
    frame.rowconfigure(i, weight=1)
for i in range(0, 5):
    frame.columnconfigure(i, weight=1)

# Bind F11 to toggle fullscreen and ESC to end fullscreen
root.bind('<F11>', toggle_fullscreen)
root.bind('<Escape>', end_fullscreen)

# Have the resize() function be called every time the window is resized
root.bind('<Configure>', resize)

# Call empty _destroy function on exit to prevent segmentation fault
root.bind("<Destroy>", _destroy)

# Call animate() function periodically
fargs = (ax1, cell_val, barrier_pos_an)
ani = animation.FuncAnimation(  fig, 
                                animate, 
                                fargs=fargs, 
                                interval=animation_interval)               

# Start in fullscreen mode and run
Tare()
#toggle_fullscreen()
root.mainloop()
