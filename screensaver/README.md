# Screensaver in Rasberry Pi

Given a list of directories containing photos of different trips or themes,
this script allows you to randomly select one and upload to a location from which a 
photo rendering app reads from, e.g. your laptop's screensaver application or 
a similar one in a RPi

# Usage

The script `screensaver.py` requires `python 3.7` with `numpy` and setting 3 environment variables:

1. `SCREENSAVER_INPUT_PATH` (The path to where the photos directories are located. Needs to end with `/`!)
2. `SCREENSAVER_OUTPUT_PATH` (The path to where to upload the photos. Should not end with `/`)
3. `SCREENSAVER_RSYNC_PORT` (The port over which ssh is being used, usually 22)

Then, you can run it with:
 
 ```
/usr/bin/python3.7 /home/pi/photo-manager/screensaver/screensaver.py
```

Alternatively you can have a bash script `run_screensaver.sh` with the following:

```
#!/bin/bash

export SCREENSAVER_INPUT_PATH="XXX" 
export SCREENSAVER_OUTPUT_PATH="XXX"
export SCREENSAVER_RSYNC_PORT="XXX"

/usr/bin/python3.7 /home/pi/photo-manager/screensaver/screensaver.py
```
Make the script executable with `chmod +x /home/pi/photo-manager/screensaver/run_screensaver.sh`. 

## Cron job

You can set `run_screensaver.sh` to run every 5 minutes via `crontab -e` and output the logging messages to a log file:

```
*/5 * * * * /home/pi/photo-manager/screensaver/run_screensaver.sh 2>/tmp/stdout_screensaver.log
```

Alternatively, you can set `run_screensaver.sh` to run every time the RPi boots by adding:

```
@reboot /home/pi/photo-manager/screensaver/run_screensaver.sh 2>/tmp/stdout_screensaver.log &
```
(Important is the '&' at the end of the line to not slow down the overall boot process too much as it now will be executed in parallel)


# Photo Rendering (Screensaver) Applications for Raspberry Pi

You can view your photos via a photo rendering application. I found the following 2 options: 

## Online photos - DAKboard

This is easy to setup as per instructions [here](https://blog.dakboard.com/diy-wall-display/)
but it only renders photos which are available online e.g. Apple Photos, Dropbox, etc.
Hence, this wasn't useful when rendering photos stored in the RPi.


## Offline photos

Based on [these](https://opensource.com/article/19/2/wifi-picture-frame-raspberry-pi) instructions. 

First run `sudo raspi-config`to configure some system options. In the configuration tool:
Go to `Boot Options > B1 > B4 Desktop Autologin (Desktop GUI)` and confirm. This might require rebooting the RPi.

Then install the lightweight app '[slide](https://github.com/NautiluX/slide/releases/tag/v0.9.0)'. 
First the dependencies:

```
sudo apt install libexif12 qt5-default
sudo apt install libexif-dev
```

Then switch into the home directory, clone the latest version and build it:

```
cd
git clone https://github.com/NautiluX/slide.git
cd slide
mkdir -p make
cd make
qmake ../src/slide.pro
make
sudo make install
```

Test run (make sure the folder `screensaver/photos` exists, if not make one using `mkdir photos` in the `screensaver` directory):

```
export DISPLAY=:0  # set the DISPLAY variable to start the slideshow on the display attached to the RPi
slide -p -t 60 -o 200 -p /home/pi/photo-manager/screensaver/photos/
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
@slide -p -t 60 -o 200 -p /home/pi/photo-manager/screensaver/photos/
```

The option `-t 60` determines how frequent the slideshow changes photos in seconds. Feel free to adjust. 

## Running the python script

### Python 3.7 environment

Ideally we want to install `python 3.7`, which is the latest stable release.
I tried to do this using `conda` by following [these instructions](https://stackoverflow.com/questions/39371772/how-to-install-anaconda-on-raspberry-pi-3-model-b), 
but this only allows to install up to `python 3.6`. Since my code was in `python 3.7`, I did not use this in the end.
Instead, I ran the code using the pre-installed `python 3.7` in the RPi OS Raspbian:

```
/usr/bin/python3.7 /home/pi/photo-manager/screensaver/screensaver.py
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
Solve by [building from scratch](https://github.com/NautiluX/slide#build) this specific commit from the 'slide'
[app](https://github.com/NautiluX/slide/commit/09fc431034a9b0c3f7ce488a7a5d4fd34593afbf).

References:
- https://github.com/NautiluX/slide/issues/6
- https://github.com/NautiluX/slide/issues/4
- https://github.com/NautiluX/slide#build

## TV switching back to RPi source
 
This was what I had to do to deactivate the HDMI-CEC commands on the RPi:
```
sudo nano /boot/config.txt
```

Add the following lines to that file:
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
