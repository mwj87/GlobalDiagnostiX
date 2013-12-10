#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script to read out the TIScamera using python.
"""

from optparse import OptionParser
import sys
import os
import shutil
import subprocess
import time
import matplotlib.pylab as plt

# Use Pythons Optionparser to define and read the options, and also
# give some help to the user
parser = OptionParser()
usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--camera", dest="camera",
                  default="tis", type='str', metavar='name',
                  help="Camera to use; at the moment 'tis', 'aptina' and "
                       "'awaiba', even when the two latter options are not "
                       "implemented yet... (default: %default)")
parser.add_option("-e", "--exposure", dest="exposuretime",
                  metavar='125', type='float',
                  help="Exposure time [ms]")
parser.add_option("-p", "--preview", dest="preview",
                  action="store_true", default=False,
                  help="Preview image (default: %default)")
parser.add_option("-s", "--suffix", dest="suffix",
                  type='str', metavar='SomeSuffix',
                  help="Suffix to add after the foldername")
parser.add_option("-t", "--time", dest="videotime",
                  default=5, type="float", metavar=12.3,
                  help="How many seconds of video shall I record? "
                  "(default: %default)")
parser.add_option("-v", "--verbose", dest="verbose",
                  action="store_true", default=False,
                  help="Be chatty. (default: %default)")
(options, args) = parser.parse_args()

if len(sys.argv[1:]) == 0:
    print "You need to enter at least one option, here's the help"
    parser.print_help()
    sys.exit()

if not options.exposuretime:
    print 'You need to supply an exposure time we should use.'
    print 'Enter the command like so:'
    print '    ', ' '.join(sys.argv), "-e exposuretime"
    sys.exit()

print 80 * "-"
print "Hey ho, let's go!"

# Check at which /dev/video we have a camera
for device in range(6):
    if os.path.exists('/dev/video' + str(device)):
        CameraPath = '/dev/video' + str(device)
        break
    else:
        if options.verbose:
            print 'Nothing found at /dev/video' + str(device)

try:
    CameraPath
except NameError:
    print 'I was not able to find a camera connected on any of /dev/video0..5'
    print 'Please make sure the camera is connected and retry.'
    sys.exit(1)
else:
    if options.verbose:
        print 'Found a camera on', CameraPath

if options.verbose:
    print "We are trying to work with the '" + options.camera + "' camera"
    print
    print "Getting available sizes"

# Get available output sizes of the currently connected camera using v4l2-ctl
process = subprocess.Popen(['v4l2-ctl', '--device=' + CameraPath,
                            '--list-formats-ext'], stdout=subprocess.PIPE)
output, error = process.communicate()
width = []
height = []
for line in output.split("\n"):
    if line and line.split()[0].startswith("Size"):
        width.append(int(line.split()[2].split("x")[0]))
        height.append(int(line.split()[2].split("x")[1]))
for size in range(len(width)):
    if options.verbose:
        print "    *", width[size], "x", height[size], "px"
if options.camera == "tis":
    CMOSwidth = max(width)
    CMOSheight = max(height)
elif options.camera == 'aptina':
    CMOSwidth = 123
    CMOSheight = 456
elif options.camera == 'awaiba':
    CMOSwidth = 123
    CMOSheight = 456
print "We are using a", CMOSwidth, "x", CMOSheight, "px detector size to",\
    "proceed."

#~ Set exposure time
#~ According to http://goo.gl/D8MHsW and http://is.gd/zaxWn7, the exposure time
#~ is set in "100 µs units, where the value 1 stands for 1/10000th of a second,
#~ 10000 for 1 second [...]". The user sets the exposure time in ms (1000 µs)
#~ 1 s = 10⁶ µs = 10⁴ units -> 1000 ms = 10⁴ units. From ms to units -> * 10
if options.verbose:
    print 'The desired exposure time is', options.exposuretime, 'ms',
else:
    print 'Setting exposure time to', options.exposuretime, 'ms'
exposureunits = options.exposuretime * 10
if options.verbose:
    print '(corresponding to', int(exposureunits), '"100 µs units").'

if options.verbose:
    process = subprocess.Popen(['v4l2-ctl', '--device=' + CameraPath, '-L'],
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    for line in output.split("\n"):
        if line and line.split()[0].startswith("exp"):
            print "The camera was set from an exposure time of",\
                line.split("=")[-1], "units",

#~ Use 'v4l2-ctl -c exposure_absolute=time' to set exposure time
process = subprocess.Popen(["v4l2-ctl", '--device=' + CameraPath,
                            "-c", "exposure_absolute=" +
                            str(exposureunits)], stdout=subprocess.PIPE)
if options.verbose:
    process = subprocess.Popen(['v4l2-ctl', '--device=' + CameraPath, '-L'],
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    for line in output.split("\n"):
        if line and line.split()[0].startswith("exp"):
            print "to", line.split("=")[-1], "units."

# Construct a general NULL pointer, used for the subprocesses
DEVNULL = open(os.devnull, 'w')
# Show the stream if desired
if options.preview:
    # Setting preview to 720p, since bigger doesn't work with mplayer
    previewwidth = 1280
    previewheight = 720
    print "I'm now showing you a", previewwidth, "x", previewheight, "px",\
        "preview image from the upper left corner of the sensor."
    # mplayer command based on TIScamera page: http://is.gd/5mJEM7
    mplayercommand = "mplayer tv:// -tv width=" + str(previewwidth) +\
        ":device=" + CameraPath + " -geometry 50%:50% -title 'Previewing" +\
        " top left edge (" + str(previewwidth) + "x" + str(previewwidth) +\
        " px), with an exposure time of " + str(options.exposuretime) +\
        " ms' -nosound"
    if options.verbose:
        print 'Previewing images with'
        print
        print mplayercommand
        print
    print "Exit with pressing the 'q' key!"
    subprocess.call(mplayercommand, stdout=DEVNULL, stderr=subprocess.STDOUT,
                    shell=True)

# Save output to a file, load that and display it.
# We save option.images images, since we often demand an image from the camera
# while it is in the middle of a circle, thus it's a corrupted image...

# Construct path
FileSavePath = os.path.join('Images', options.camera, str(int(time.time())))
if options.suffix:
    FileSavePath += '_' + str(options.suffix)
if options.exposuretime:
    FileSavePath += '_' + str(options.exposuretime) + 'ms'
try:
    # Generating necessary directories
    os.makedirs(FileSavePath)
except:
    print FileSavePath, 'cannot be generated'
    sys.exit(1)

# Use ffmpeg to save video stream to lossless video, then extract single frames
# from this video
print 'Saving', options.videotime, 'seconds of video',
# Exposure time in ms -> theoretical FPS
TheoreticalFPS = 1000 / options.exposuretime
print 'with (theoretically)', round(TheoreticalFPS, 2), 'fps'
if TheoreticalFPS > 7.5:
    print 'According to "v4l2-ctl --list-formats-ext" we can reach 7.5 fps',\
        'max.'

# Command based on https://trac.ffmpeg.org/wiki/x264EncodingGuide#LosslessH.264
# ffmpeg -i input -c:v libx264 -preset ultrafast -qp 0 output.mkv
ffmpegcommand = "ffmpeg -y -f video4linux2 -s " + str(CMOSwidth) + "x" +\
    str(CMOSheight) + " -i " + CameraPath + " -vcodec libx264 -vpre " +\
    "ultrafast -qp 0 -t " + str(options.videotime) + " " + \
    os.path.join(FileSavePath, 'video.mkv')

# -preset ultrafast -qp 0 -> lossless
# -t $time$ -> save $time$ seconds of video
# -y overwrite always
if options.verbose:
    print 'Recording video with'
    print 20 * '-'
    print ffmpegcommand
    print 20 * '-'
print 'Saving video now!'
print 'Please stand by for at least', int(round(options.videotime)),\
    'seconds...'
print 'Press the trigger while doing this!'
t0 = time.time()
subprocess.call(ffmpegcommand, stdout=DEVNULL, stderr=subprocess.STDOUT,
                shell=True)
t1 = time.time()
if t1 - t0 < options.videotime:
    print
    print 'It seems that I was saving faster than possible, the process',\
        'probably failed'
    print 'I am deleting', FileSavePath
    print
    print 'Please restart acquisition by repeating your last command.'
    shutil.rmtree(FileSavePath)
    sys.exit(1)
print "Recording and saving the video took me", str(round(t1 - t0, 2)),\
    "seconds"

# Converting above video to tiff-files
convertcommand = "ffmpeg -i " + os.path.join(FileSavePath, 'video.mkv') +\
    " -pix_fmt gray " + os.path.join(FileSavePath, 'frame_%05d.tif')
if options.verbose:
    print 'Converting video to images with'
    print 20 * '-'
    print convertcommand
    print 20 * '-'

print 'Converting the video into single frames'
t0 = time.time()
subprocess.call(convertcommand, stdout=DEVNULL, stderr=subprocess.STDOUT,
                shell=True)
t1 = time.time()
print "Converting the video took me", str(round(t1 - t0, 2)), "seconds"

# Save 'Log'-file
logfile = open(os.path.join(FileSavePath, '_log.txt'), "w")
logfile.write('The files in this directory were generated by this command:\n')
logfile.write(' '.join(sys.argv))
logfile.close()

print
print 'In the directory', FileSavePath, 'you now have'
print '    * a logfile (_log.txt)'
print '    * the raw video from the camera (video.mkv)'
# Count only certain files (http://stackoverflow.com/a/1321138)
NumberOfFrames = len([f for f in os.listdir(FileSavePath)
                     if f.endswith('.tif') and
                     os.path.isfile(os.path.join(FileSavePath, f))])
print '    * and', NumberOfFrames, 'frames of the video (frame*.tif), thus',\
    'a (calculated)', str(round(NumberOfFrames / options.videotime, 2)), 'fps.'
print 'Have fun with this!'

print 80 * "-"
print "done"
