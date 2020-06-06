# Screensaver in Rasberry Pi

Given a list of directories containing photos of different trips or themes,
this script allows you to randomly select one and upload to a location from which a 
photo rendering app reads from, e.g. your laptop's screensaver application or 
a similar one in a Raspberry Pi

# Usage

The script `screensaver.py` requires `python 3.7` and setting 2 environment variables:
`SCREENSAVER_INPUT_PATH` (the path to where the photos directories are located) and
`SCREENSAVER_OUTPUT_PATH` (the path to where to upload the photos so the photo rendering app can read from).
 Then, you can run as:
 
 ```
/usr/bin/python3.7 /home/pi/code/photo-manager/screensaver/screensaver.py
```

Alternatively you can have a bash script `run_screensaver.sh` with the following:

```
#!/bin/bash

export SCREENSAVER_INPUT_PATH=XXX 
export SCREENSAVER_OUTPUT_PATH=XXX

/usr/bin/python3.7 /home/pi/code/photo-manager/screensaver/screensaver.py
```

## Cron job

I set `run_screensaver.sh` to run every 5 minutes via `crontab -e` and output the logging messages to a log file:

```
*/5 * * * * /usr/bin/python3.7 /home/pi/screensaver/screensaver.py 2>/tmp/stdout_screensaver.log
```


# Photo Rendering (Screensaver) Applications for Raspberry Pi

You can view your photos via a photo rendering application. I found the following 2 options: 

## Online photos - DAKboard

This is easy to setup as per instructions here: https://blog.dakboard.com/diy-wall-display/
but it only renders photos which are available online e.g. Apple Photos, Dropbox, etc.
Hence, this wasn't useful when rendering photos stored in the RPi.


## Offline photos

Followed instructions here https://opensource.com/article/19/2/wifi-picture-frame-raspberry-pi

First I ran `raspi-config`to configure some system options. Once in the configuration tool:
Go to `Boot Options > Desktop Autologin Desktop GUI` and press `Enter`.

The install this lightweight slideshow app https://github.com/NautiluX/slide/releases/tag/v0.9.0

```
wget https://github.com/NautiluX/slide/releases/download/v0.9.0/slide_pi_stretch_0.9.0.tar.gz
tar xf slide_pi_stretch_0.9.0.tar.gz
mv slide_0.9.0/slide /usr/local/bin/
```

Install the dependencies:

```
sudo apt install libexif12 qt5-default
```

Test run:

```
export DISPLAY=:0  # set the DISPLAY variable to start the slideshow on the display attached to the Raspberry Pi
slide -p -t 60 -o 200 -p /home/pi/code/photo-manager/screensaver/photos/
```
Then, kill this process and now force the screen to stay on and run the slide app automatically by editing this file:

```
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

and add 

```
lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash

# added for screenserver app
@xset s noblank
@xset s off
@xset -dpms
@slide -p -t 60 -o 200 -p /home/pi/code/photo-manager/screensaver/photos/
```


## Running the python script

### Python 3.7 environment

Ideally we want to install `python 3.7`, which is the latest stable release.
I tried to do this using `conda` by following this instructions
https://stackoverflow.com/questions/39371772/how-to-install-anaconda-on-raspberry-pi-3-model-b
but this only allows to install up to `python 3.6`. Since my code was in `python 3.7`, I didn't use this in the end.
Instead, I ran the code using the pre-installed `python 3.7` in the RPi OS Raspbian:

```
/usr/bin/python3.7 /home/pi/screensaver/screensaver_rpi.py
```

# Errors

## Display error

```
No protocol specified
qt.qpa.screen: QXcbConnection: Could not connect to display :0
Could not connect to any X display.
```
Solve this by exporting the display variable:

```
export DISPLAY=:0 
```

## Floating point exception

```
libEGL warning: DRI2: failed to authenticate
Floating point exception
```
Solve by [building from scratch](https://github.com/NautiluX/slide#build) this commit from the `slide` app: 
https://github.com/NautiluX/slide/commit/09fc431034a9b0c3f7ce488a7a5d4fd34593afbf

```
sudo apt install libexif-dev
mkdir -p make
cd make
qmake ../src/slide.pro
make
sudo make install
```

References:
- https://github.com/NautiluX/slide/issues/6
- https://github.com/NautiluX/slide/issues/4
- https://github.com/NautiluX/slide#build

## TV switching back to RPi source
 
This was what I had to do to deactivate the HDMI-CEC commands on the rpi.
Added the following lines to my /boot/config.txt  :

```
hdmi_ignore_cec_init=1
hdmi_ignore_cec=1
```


More info [here](https://elinux.org/RPiconfig). This might not work perfectly, and a TV can still get confused. 
In that case following hardware is required:
[HDMI CEC Less Adapter](https://www.amazon.co.uk/LINDY-HDMI-Less-Adapter-Female-Black/dp/B00DL48KVI). 
This will terminate pin 13 of the HDMI cable, which is responsible for the CEC signal.

# Other references

- https://www.cnet.com/how-to/turn-an-old-monitor-into-a-wall-display-with-a-raspberry-pi/
- https://pimylifeup.com/raspberry-pi-photo-frame/
