# -*- coding: utf-8 -*-


from pyvisa_drivers import Keithley2401, NewportMM4005
import os
from os.path import join
from time import sleep, time
import matplotlib.pyplot as plt
import numpy as np


#-----------------------------------------------------------------------------#
# Functions
#-----------------------------------------------------------------------------#

def not_at_stopping_angle(current_angle, final_angle, delta):
    if np.sign(delta) == 1.0:
        return current_angle <= final_angle
    else:
        return current_angle >= final_angle


#-----------------------------------------------------------------------------#
# Parameters
#----------------------------------------------------------------------------#
sample = 'B936_2'
date = '160407'
temp = '295'  # Kelvin
field_strength = '2000'  # Gauss
rotate_there_and_back = False
rootdir = r'F:\Rzchlab\Google Drive\BiFe'
workingdir = join(rootdir, sample, 'r_vs_angle', date)


start_angle = -170
end_angle = 140
angle_inc = 3
measurements_per_angle = 2


keithley_2401_addr = 20
newport_mm4005_addr = 2
newport_mm4005_axis = 3


#-----------------------------------------------------------------------------#
# Interactive
#-----------------------------------------------------------------------------#
prompt = 'Enter measurement ID number (prepended to data directory name): '
id_str = input(prompt)
fmtstr = '{id!s}_{field!s}G_{temp!s}K_{start!s}to{end!s}deg_by{inc!s}'
data_dir = fmtstr.format(id=id_str, field=field_strength, temp=temp,
                         start=start_angle, end=end_angle, inc=angle_inc)
input('OK? -- ' + data_dir)
savedir = join(workingdir, data_dir)
os.mkdir(savedir)
os.chdir(savedir)


#-----------------------------------------------------------------------------#
# Initialize
#-----------------------------------------------------------------------------#
# Setup GPIB connections
sm = Keithley2401(keithley_2401_addr)
mc = NewportMM4005(newport_mm4005_addr, newport_mm4005_axis)


# Move to starting positions
current_angle = start_angle
velocity = mc.get_velocity()
wait_time = abs(mc.get_position() - current_angle) / velocity + 5
mc.motor_on()
mc.move_to(start_angle)
print("Waiting {}s for motion controller to reposition".format(wait_time))
sleep(wait_time)

# create data file
data_table_file = 'data_table.txt'
data_table = []

# Real time plotting
plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel("Angle (Degrees)")
ax.set_ylabel("Resistance ($\Omega$)")
fig.tight_layout()
rt_x = []
rt_y = []


#-----------------------------------------------------------------------------#
# Main loop
#-----------------------------------------------------------------------------#


start_time = time()
current_angle = start_angle

while not_at_stopping_angle(current_angle, end_angle, angle_inc):
    print(str(current_angle) + ' Degrees')
    mc.move_to(current_angle)
    sleep(abs(angle_inc/velocity))
    raw = np.array(sm.read_resistances(measurements_per_angle))
    resistance = raw.mean()
    data_table.append([current_angle, resistance])

    rt_x.append(current_angle)
    rt_y.append(resistance)
    l = ax.scatter(rt_x, rt_y, c='r', linewidths=0, s=40)
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)

    current_angle += angle_inc
    sleep(0.2)

if rotate_there_and_back:
    while not_at_stopping_angle(current_angle, start_angle, -angle_inc):
        print(str(current_angle) + ' Degrees')
        mc.move_to(current_angle)
        sleep(abs(angle_inc/velocity))
        raw = np.array(sm.read_resistances(measurements_per_angle))
        resistance = raw.mean()
        data_table.append([current_angle, resistance])

        rt_x.append(current_angle)
        rt_y.append(resistance)
        l = ax.scatter(rt_x, rt_y, c='r', linewidths=0, s=40)
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)

        sleep(0.2)


#-----------------------------------------------------------------------------#
# Save and clean up
#-----------------------------------------------------------------------------#

header = '\t\t'.join(['Angle', 'R'])
np.savetxt(data_table_file, data_table, header=header)
plt.savefig("r_vs_angle.png", dpi=144)


mc.motor_off()

d = np.array(data_table)
r = d[:, 1]
angle = d[:, 1]
print('|AMR| = {:.3e}'.format(r.max() - r.min()))
print('AMR% = {:.3e}'.format((r.max() - r.min())/(r.mean())))
print('angle[argmax(r)] = {}'.format(angle[np.argmax(r)]))
print('angle[argmin(r)] = {}'.format(angle[np.argmin(r)]))


runtime_s = int(time() - start_time)
print("Runtime: %d min %d sec" % (runtime_s//60, runtime_s % 60))
