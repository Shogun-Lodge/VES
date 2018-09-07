
"""
ves.py

Video playback, headphone selection monitoring and data logging system.

Orginally conceived by Rob Larsen

By Marcus Cook <tech@theshogunlodge>
Shogun Lodge Services
2017

Thanks to the authors of all libraries/wrappers used.

Shogun Lodge Services acknowledges the traditional owners and custodians of the 
land on which it works, the Wurundjeri people of the Kulin Nation. It pays 
respects to their Elders both past and present and acknowledges that 
sovereignty has never been ceded.

'All spelling mistakes are intentional and quite witty'  

TBD -
Get rid of Globals (and stop coding like it's C++)
Visual/LED indicators
Config File Reading
Logging
	>Boot date and time stamp
	>Headphone status
		>On/Off
		>Time On
		>Time Off
		>Average On
		>Average Off
	>DAC Staus
	>HDMI Staus
	>Video Pos
	>Video File Name
	>CPU Load
	>CPU Temp
OSC Control and Enquiry (JSON)
Web Server based config

"""

#!/usr/bin/python

import sys
import subprocess
import time
import RPi.GPIO as GPIO

from omxplayer import OMXPlayer
from time import sleep

GPIO.setmode(GPIO.BCM)

# \/\/-Variables-\/\/

# --GPIO--
RED_LED = 0			# Title video LED
GRN_LED = 1			# Main video LED
SWITCH1 = 13			# Headphone switch 1
SWITCH2 = 12			# Headphone switch 2
EXIT = 26			# Exit button

# --Switch State--
skip = 0			# Skip flag - Stops main video reloading itself when 'fade down' aborted
global hpCnt			# Headphone count - Number of times headphone has been used


# --Video Locations--
vidA = '/home/pi/video/title_card.mp4'
vidB = '/home/pi/video/video.mp4'

# --Log Files--
logFile = "/home/pi/log/ves_log.txt"				# Log file  - Count of headphone use
global cursor

# --Time Measurments--
global hpUp
hpUp = 0.0
global totalUp
totalUp = 0.0
global averUp
averUp = 0.0
global timeUp
timeUp = 0.0

# \/\/-Set Ups-\/\/

GPIO.setup(SWITCH1, GPIO.IN, pull_up_down=GPIO.PUD_UP)		# Switch pulled up
GPIO.setup(SWITCH2, GPIO.IN, pull_up_down=GPIO.PUD_UP)		# Switch pulled up
GPIO.setup(EXIT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(RED_LED, GPIO.OUT)					# LED indicator setup
GPIO.setup(GRN_LED, GPIO.OUT)
GPIO.output(GRN_LED,GPIO.LOW)
GPIO.output(RED_LED,GPIO.HIGH)

player = OMXPlayer(vidA, args=['-o', 'alsa:hw:1,0', '--no-osd', '-b', '--loop', '--alpha', '0']) # First on 'Title Card'
#player = OMXPlayer(vidA, args=['--no-osd', '-b', '--loop', '--alpha', '0'])
player.set_aspect_mode("fill")

date=subprocess.check_output("date",  shell=True)	# Read internal clock

hpCnt = 0

# Open log file and write in time and date of boot up
with open(logFile, 'a') as file:
	#file.seek(0)
	file.write('\n')
	file.write(date)
	file.write('\n')
	cursor = file.tell()
	print "Cursor Pos = {0:5}".format(cursor)

# \/\/-Functions-\/\/

# Read states of heaphone switches
def switch_state():
	ip1 = GPIO.input(SWITCH1)
	ip2 = GPIO.input(SWITCH2)

	if (ip1 == 1) or (ip2 == 1):		# Is either heaphone 'up'?
		time.sleep(0.010)		# Debounce
		if (ip1 == 1) or (ip2 == 1):
			x = int(1)		# Value to return
	
	if (ip1 == 0) and (ip2 == 0):		# Are both headphones down?
		time.sleep(0.010)
		if (ip1 == 0) and (ip2 == 0):
			x = int(0)
	return x

# Fades currnet video down. 'dwn' is the range jump amount and controls speed of fade
# 'flag' is so possiable fade back up only happens in main video
def vidDwn(dwn, flag):
	print "Fading Down..."			# Testing
	start = time.time()			# Testing - Start timer
	for alpha in range(254, -1, dwn):       # Fade loop
		x = switch_state()		# Has headphone been picked up?
		if(x == 1) and (flag == 1):	# If hp up and in main video start fading back up
			print "Hold On!"	# Testing
			vidUp(alpha, 2)
			skip = 1		# Set skip flag
			log()			# Log event
			return skip
		player.set_alpha(alpha)		# Set video alpha
		vol = float(alpha)		
		vol = ((vol/0.0425)-6000.0) 	# Make volume value relative to alpha value
		player.set_volume(vol)		# Set audio volume
	player.quit()				# Stop video
	print "Video Stop"			# Testing
	elapsed = (time.time() - start)		# Testing - Stop timer
	print "Alpha = {0:3d}".format(alpha)	# Testing
	realVol = (vol / 100)			# Testing
	print "Vol = {0:2.2f}db".format(realVol)
	print "Time Taken = {0:2.2f} Sec.".format(elapsed)				# Testing
	skip = 0				# Set skip flag
	return skip				

# Fades just started video up. 's' is start of fade alpha value
# 'up is the range jump amount and controls speed of fade
def vidUp(s, up):
	print "Fading Up..."			# Testing
	start = time.time()			# Testing - Start timer
        for alpha in range(s, 256, up):		# Fade loop
		player.set_alpha(alpha)		# Set video alpha
                vol = float(alpha)		
                vol = ((vol/0.0425)-6000.0)	# Make volume value relative to alpha value
                player.set_volume(vol)		# Set audio volume
	print "Video Up"			# Testing
        elapsed = (time.time() - start)		# Testing - Stop timer
        print "Alpha = {0:3d}".format(alpha)				# Testing
	realVol =  (vol / 100)			# Testing
	print "Vol = {0:2.2f}db".format(realVol)
	print "Time Taken = {0:2.2f} Sec.".format(elapsed)				# Testing

# Logs headphone 'up' events
def log():
	with open(logFile, 'r+') as file:
		file.seek(cursor)
		print "Cursor HP Log Pos = {0:5}".format(cursor)
		file.write('Headphone count = {0:3d}'.format(hpCnt))
		file.write('\n')
		file.write('Last Up Time = {0:6.2f} Sec.'.format(hpUp))
		file.write('\n')
		file.write('Average Up Time = {0:6.2f} Sec.'.format(averUp))
		file.write('\n')
		file.write('Total Up Time = {0:8.2f} Sec.'.format(totalUp))
		file.write('\n')
		file.write('\n')

# Maths for logging usage times, averages, etc...
def times():
	global totalUp
	totalUp = (totalUp + hpUp)			# Calculate new total 'UP' time
	global averUp
	averUp = (totalUp / hpCnt) 			# Calculate new average 'UP' time
	print "Last Up Time = {0:4.2f} Sec.".format(hpUp)
        print "Average Up Time = {0:6.2f} Sec.".format(averUp)
	print "Total Up Time = {0:6.2f} Sec.".format(totalUp)
	log()						# Log file

# Exits script with button press
def interrupt(channel):
	player.quit()
        GPIO.cleanup()
        print ' '
        print "See Ya Later Button Pressed (>'.')>"
        exit("Interrupt Exit")

# \/\/-Main Code-\/\/

# Play 'Title Card'
player.set_alpha(255)
time.sleep(0.5)
player.play()
time.sleep(0.5)
player.pause()

GPIO.add_event_detect(EXIT, GPIO.FALLING, callback=interrupt, bouncetime=200) 

print "State A Video Displayed"			# Testing

print "Here we go... HP Switches Active"		# Testing

try:
	while(1):
		while(1):			
			a = switch_state()						# Test headphone switch state
			if(a != 0):							# If a headphone 'up'
                        	hpCnt = hpCnt+1               				# +1 headphone count    
                        	print ("Headphone count = {a:3d}".format(a=hpCnt))	# Testing
				log()							# Log event
				break
                
		if(skip == 0):										# If 'Title Card' is up
			print 'State B Video Selected'							# Testing
        		vidDwn(-6,0)									# Fade 'Title Card' ~ 2 sec.
			player = OMXPlayer(vidB, args=['-o', 'alsa:hw:1,0', '--no-osd', '-b', '--loop', '--alpha', '0'])	# Main video
			#player = OMXPlayer(vidB, args=['--no-osd', '-b', '--loop', '--alpha', '0'])
			player.set_volume(-6000.0)							# Volume = -60dB
        		player.set_aspect_mode("fill")							# Set aspect
			#global timeUp
			timeUp = time.time()								# Start timing UP
			vidUp(1,12)									# Fade up ~ 1 sec
		GPIO.output(RED_LED,GPIO.LOW)
		GPIO.output(GRN_LED,GPIO.HIGH)
		skip = 0										# Clear skip flag

        	while(1):
        		b = switch_state()								# Test headphone switch state
			if(b != 1):									# If both headphones down
				break

		print 'State A Video Selected'								# Testing	
		hpUp = (time.time() - timeUp)								# Latest UP time
		print "HP Up time = {0:8.2}".format(hpUp)						# Testing
		times()											# Time maths and log
		skip = vidDwn(-8,1)                                                                     # Fade main video ~ 2 Sec
		#skip = vidDwn(-2,1)									# Fade main video ~ 6 Sec
		if(skip == 0):										# If main video has completely faded
			print "Skip = 0"								# Testing
			player = OMXPlayer(vidA, args=['-o', 'alsa:hw:1,0', '--no-osd', '-b', '--loop', '--alpha', '0'])	# 'Title Card'
			#player = OMXPlayer(vidA, args=['--no-osd', '-b', '--loop', '--alpha', '0'])
			player.set_aspect_mode("fill")							# Set aspect
			player.set_volume(-6000.0)							# Volume = -60dB
			time.sleep(0.5)								
			player.pause()									# Pause 'Title Card'
			vidUp(1,6)									# Fade up ~ 2 Sec
                	GPIO.output(GRN_LED,GPIO.LOW)
			GPIO.output(RED_LED,GPIO.HIGH)

except KeyboardInterrupt:
	player.quit()
	GPIO.cleanup()
	print ' '
	print " CTRL+C = Ciao (o^-^o)"
	sys.exit()


#except:
#        player.quit()
#	GPIO.cleanup()
#        print ' '
#        print "Dbus Sad :'("
#        sys.exit()
