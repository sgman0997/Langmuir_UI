import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import RPi.GPIO as GPIO
from hx711 import HX711
import time
import sys
from guizero import App, Text

#app = App(title="IRVING")


referenceUnit = 1

#def cleanAndExit():
#    print("Cleaning...")
#    GPIO.cleanup()
#    print("Bye!")
#    sys.exit()



hx1 = HX711(5, 6)
#hx2 = HX711(13, 19)
hx1.set_reading_format("MSB", "MSB")
hx1.reset()
hx1.tare()
ave = hx1.read_average(10)
#hx2.set_reading_format("MSB", "MSB")
#hx2.reset()
#hx2.tare()

#print("Tare done! Add weight now...")
# to use both channels, you'll need to tare them both
#hx.tare_A()
#hx.tare_B()

# Create figure for plotting
fig = plt.figure()
#ax = fig.add_subplot(1, 1, 1)
#xs = []
#y1 = []
#y2 = []

ax1 = fig.add_subplot(1, 1, 1)
ax1.set_ylabel('cell 1', color='tab:red')
ax1.tick_params(axis='y', labelcolor='tab:red')
# Instantiate a new set of axes that shares the same x-axis
#ax2 = ax1.twinx()
#ax2.set_ylabel('cell 2', color='tab:blue')
#ax2.tick_params(axis='y', labelcolor='tab:blue')
x_len = 500
y_min = (ave - 100000)
y_max = (ave + 100000)
y_range = [y_min, y_max]
xs = list(range(0, x_len))
y1 = [0] * x_len
#ax1.set_ylim(y_range)
line1, = ax1.plot(xs, y1)
#line2, = ax2.plot(xs, y2)

    
# Format plot
#plt.xticks(rotation=45, ha='right')
#plt.subplots_adjust(bottom=0.30)
plt.title('samples')
plt.ylabel('surface pressure')

# This function is called periodically from FuncAnimation
def animate(i, y_range, y1):
    #ymin = y_min
    #ymax = y_max
    # Read value
    wval1 = hx1.read_long()
    print(wval1)
    #wval2 = hx2.get_weight(1)
        # the occasional -1 will be encountered by the serial input and should be ignored
    #if wval < 1*10**5 and wval > -1*10**5:
    # Add x and y to lists
        #wval = hx.get_weight(1)
    #xs.append(dt.datetime.now())
    y1.append(wval1)
    #y2.append(wval2)
    y1 = y1[-x_len:]
    
    line1.set_ydata(y1)
    #if wval1 < y_range[0] or wval1 > y_range[1]:
    ymin = (wval1 - 100000)
    ymax = (wval1 + 100000)
    #y_range = [ymin, ymax]
    ax1.set_ylim([ymin, ymax])
    #ax1.tick_params(axis='y')
    #ax1.set_ylabel('surface pressure', color='tab:red')
    #line1.set_xdata(xs)
    # Limit x and y lists 
    #xs = xs[-20:]
    #ys = ys[-20:]

    # Draw x and y lists
    #ax.clear()
    #ax.plot(xs, ys)

    color = 'tab:red'
    ax1.clear()
    ax1.set_ylabel('cell 1', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.plot(xs, y1, linewidth=2, color='tab:red')
    #ax1.plot(xs, y1)
    
    #ax1.fill_between(xs, temps, 0, linewidth=2, color=color, alpha=0.3)

    # Clear, format, and plot temperature values (in front)
    #color = 'tab:blue'
    #ax2.clear()
    #ax2.set_ylabel('cell 2', color=color)
    #ax2.tick_params(axis='y', labelcolor=color)
    #ax2.plot(xs, y2, linewidth=2, color=color)

    # Format plot
    #plt.xticks(rotation=45, ha='right')
    #plt.subplots_adjust(bottom=0.30)
    #plt.title('samples')
    #plt.ylabel('surface pressure')
    
    return line1,


# Set up plot to call animate() function periodically
#ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
#plt.show()
def blit_graph():
    ani = animation.FuncAnimation(fig, animate, fargs=(y_range, y1,), interval=10, blit=True)
    plt.show()

#while 1:
#    wval1 = hx1.read_long()
#    print(wval1)
#    y1.append(wval1)
#    y1 = y1[-x_len:]
    
    
#app.display()
