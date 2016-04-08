# -*- coding: utf-8 -*-

# Standard Library
import os
from time import sleep, time

# Instruments
from pyvisa_drivers import Keithley2401
from c_newportMM4005 import NewportMM4005

# Scientific Python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc_file
rc_file(r'F:\Julian\Dropbox\Configs\jji_simple.rc')

# Julian's Code
from libjji import loadcsv
from MetadataWriter import MetadataWriter

###########################
#     INPUT VARIABLES     #
###########################

ps = {
  'AUTO': True,
  'WRITE_OUT_PLOTS': True,
  'ROTATE_THERE_AND_BACK': False,
  'PLOT_V_INSTEAD_OF_R': False,
  'root_data_dir': r'F:\Rzchlab\Google Drive\BiFe\B936_2\r_vs_angle\160406',
  # Sample Information
  'SAMPLE_ID': 'B936_2',
  'SAMPLE_PAD': '',
  'ANGLE_OF_CURRENT': '',  # w.r.t sample long edge
  'ANGLE_OF_EASY_AXIS': '',  # w.r.t current
  # Experimental Parameters
  'STARTING_ANGLE': -170,  # Motor Coords
  'ENDING_ANGLE': 140,  # Motor Coords
  'ANGLE_OFFSET': 0,  # For Plotting
  'ANGLE_INCREMENT': 3,
  'PROBE_ROTATION_DIRECTION': 'CCW',  # Looking at the cryostat from above,
  'TEMPERATURE': '295',
  'FIELD_STRENGTH': '2000'  # Gauss
}

# Motion Controller
mc_ps = {
  'UNITS': 'degrees',
  'VELOCITY': 10,  # Units/Sec.,
  'STARTING_ANGLE': ps['STARTING_ANGLE'],
  'ENDING_ANGLE': ps['ENDING_ANGLE']
}


###########################
#        FUNCTIONS        #
###########################

def update_axarr_lims(axarr):
    for ax in axarr:
        ax.relim()
        ax.autoscale_view()

####################################
# Initial Instrument Configuration #
####################################

# Go to working directory of choice
print("Finding_root_data_dir...")
os.chdir(ps['root_data_dir'])

# Motion Controller
print("Configure Motion Controller...")
mc = NewportMM4005(2, 3)
mc.motor_off()
mc.set_units(mc_ps['UNITS'])
mc.set_velocity(mc_ps['VELOCITY'])

###########################
#        MAIN LOOP        #
###########################

# Make the user review the most important information
print('PLEASE CONFIRM EXPERIMENTAL PARAMETERS ARE CORRECT [press any key]')
input('Magnetic Field: ' + str(ps['FIELD_STRENGTH']))
input('Temperature: ' + str(ps['TEMPERATURE']))
input('Root Data Directory: ' + ps['root_data_dir'])
input('Sample Name: ' + str(ps['SAMPLE_ID']))
input(str(ps['STARTING_ANGLE']) + 'deg to ' + str(ps['ENDING_ANGLE']) +
      'deg by ' + str(ps['ANGLE_INCREMENT']))

# Ask for measurement ID num and then display the generated
# directory name
prompt = 'Enter measurement ID number (prepended to data directory name): '
id_str = input(prompt)
fmtstr = '{id!s}_{field!s}G_{temp!s}K_{start!s}to{end!s}deg_by{inc!s}'
data_dir = fmtstr.format(
  id=id_str,
  field=ps['FIELD_STRENGTH'],
  temp=ps['TEMPERATURE'],
  start=ps['STARTING_ANGLE'],
  end=ps['ENDING_ANGLE'],
  inc=ps['ANGLE_INCREMENT'])
input('OK? -- ' + data_dir)
os.mkdir(os.path.join(ps['root_data_dir'], data_dir))
os.chdir(os.path.join(ps['root_data_dir'], data_dir))

# Move to starting positions
current_angle = ps['STARTING_ANGLE']
wait_time = abs(mc.get_position() - current_angle) / mc_ps['VELOCITY'] + 2
mc.motor_on()
mc.move_to(ps['STARTING_ANGLE'])
print("Waiting {0}s for motion controller to reposition".format(wait_time))
sleep(wait_time)

# Initialize data file
data_table_file = open('data_table.txt', 'w')
data_table = []

# Realtime Plotting
plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel("Angle (Degrees)")
ax.set_ylabel("Resistance ($\Omega$)")
fig.tight_layout()
rt_x = []
rt_y = []

start_time = time()


def not_at_stopping_angle(current_angle, final_angle, delta):
    if np.sign(delta) == 1.0:
        return current_angle <= final_angle
    else:
        return current_angle >= final_angle

while not_at_stopping_angle(
  current_angle, ps['ENDING_ANGLE'], ps['ANGLE_INCREMENT']):

    print(str(current_angle) + ' Degrees')

    # Move motion controller to next angle
    mc.move_to(current_angle)
    sleep(abs(ps['ANGLE_INCREMENT'])/mc_ps['VELOCITY'] + 0.25)

    # Measure up resistance
    print("    Measuring resistance: u1")
    raw = np.array(sm.read_resistances(sm_ps['NUM_POINTS'], sm_ps['CURRENT']))
    resistance = np.average(raw)
    std_dev = np.std(raw)

    # Update Realtime Plot
    rt_x.append(current_angle + ps['ANGLE_OFFSET'])
    rt_y.append(resistance)
    l = ax.scatter(rt_x, rt_y, c='r', linewidths=0, s=40)
    ax.ticklabel_format(useOffset=False)
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)

    data_row = [current_angle + ps['ANGLE_OFFSET'], resistance, std_dev]
    data_table.append(data_row)
    current_angle += ps['ANGLE_INCREMENT']
    sleep(0.2)

if ps['ROTATE_THERE_AND_BACK']:
        # Now rotate back the other way
    while not_at_stopping_angle(
      current_angle, ps['STARTING_ANGLE'], -ps['ANGLE_INCREMENT']):

        print(str(current_angle) + ' Degrees')

        # Move motion controller to next angle
        mc.move_to(current_angle)
        sleep(abs(ps['ANGLE_INCREMENT'])/mc_ps['VELOCITY'] + 1)

        # Measure up resistance
        print("    Measuring resistance: u1")
        raw = np.array(sm.read_resistances(sm_ps['NUM_POINTS'], sm_ps['CURRENT']))
        resistance = np.average(raw)
        std_dev = np.std(raw)

        # Update Realtime Plot
        rt_x.append(current_angle + ps['ANGLE_OFFSET'])
        rt_y.append(resistance)
        l = ax.scatter(rt_x, rt_y, c='r', linewidths=0, s=40)
        ax.ticklabel_format(useOffset=False)
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)

        data_row = [current_angle + ps['ANGLE_OFFSET'], resistance, std_dev]
        data_table.append(data_row)
        current_angle += -ps['ANGLE_INCREMENT']
        sleep(2)

# Clean up
mc.motor_off()
plt.ioff()
np.savetxt(
  data_table_file,
  data_table,
  fmt='%.8e',
  delimiter='\t',
  header='\t\t'.join(['Angle', 'R', 'Std'])
)
data_table_file.close()

# Plot dR data
angle, r = loadcsv("data_table.txt", [0, 1], cols=True)
plt.clf()
fig, ax = plt.subplots()
ax.set_xlabel("Angle (Degrees)", fontsize=26)
ax.set_ylabel("Resistance ($\Omega$)", fontsize=26)
ax.scatter(angle, r, c='r', linewidths=0, s=40)
ax.plot(angle, r, 'r--', label='Up')
plt.ticklabel_format(useOffset=False)
plt.tight_layout()
plt.savefig("r_vs_angle.png", dpi=144)

try:
    print('|AMR| = {:.3e}'.format(r.max() - r.min()))
    print('AMR% = {:.3e}'.format((r.max() - r.min())/(r.mean())))
    print('angle[argmax(r)] = {}'.format(angle[np.argmax(r)]))
    print('angle[argmin(r)] = {}'.format(angle[np.argmin(r)]))
except Exception:
    print('Failed to compute and print AMR stats')

# Write out metadata
ps_mdw = MetadataWriter(ps, title="Experimetnal Parameters")
sm_mdw = MetadataWriter(sm_ps, title="Source Meter Parameters")
mat_mdw = MetadataWriter(mat_ps, title="Switch Matrix Parameters")
mc_mdw = MetadataWriter(mc_ps, title="Motion Controller Parameters")
mdws = [ps_mdw, sm_mdw, mat_mdw, mc_mdw]
md_filename = 'metadata.txt'
for mdw in mdws:
    mdw.dump_to_file(md_filename)

os.chdir(ps['root_data_dir'])
runtime_s = int(time() - start_time)

print("Runtime: %d min %d sec" % (runtime_s//60, runtime_s % 60))
