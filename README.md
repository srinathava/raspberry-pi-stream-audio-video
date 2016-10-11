# Streaming Live Video and Audio from a Raspberry Pi to a browser

This setup shows how to a stream a live video/audio stream from a Rasbperry Pi to any browser with a pretty low latency. This setup was tested with a Logitech C270 camera connected to a Raspberry Pi 2. 

## Setup
### Upgrade Raspberry Pi
Depending on how old your Raspberry Pi is, you might need to do an apt-get update/upgrade in order to be able to compile Janus (which is not available on apt as of this writing). On a terminal:

    sudo apt-get update
    sudo apt-get upgrade
    
This takes a while, so be patient.

### Setup gstreamer
This should be pretty simple since its available on apt. You can do:

    sudo apt-get install gstreamer-1.0
    
to install it.

### Setup Janus
Janus provides a way to convert an audio-stream obtained from the webcam into a WebRTC stream which is understood by many modern browsers. Unfortunately, Janus is not available as a debian package as of now. Following the instructions from here, you need to do:

     cd ~
     mkdir janus && cd janus
     
