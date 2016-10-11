#!/bin/sh

# The following gstreamer pipeline(s) 
# 1. broadcast OPUS encoded audio to UDP port 5002 which is then converted
#    to a WebRTC stream by Janus 
# 2. broadcast raw JPEG frames to TCP port 9999. This is then read in by
#    the mpeg_server.py script and packaged into a multi-part stream so
#    that a browser can display it
gst-launch-1.0 \
    alsasrc device=plughw:1,0 \
        ! audioresample \
        ! audio/x-raw,channels=1,rate=16000 \
        ! opusenc bitrate=20000 \
        ! rtpopuspay \
        ! udpsink host=127.0.0.1 port=5002 \
    v4l2src device=/dev/video0 \
        ! video/x-raw,framerate=15/1, width=640, height=480 \
        ! jpegenc \
        ! multipartmux boundary=spionisto \
        ! tcpclientsink host=127.0.0.1 port=9999 
