Python script to for Chime Video Reconstruction
---

Basic usage:
* Download a recording
* Run this script
* Get an `output.mp4`

To download, I recomment using `aws s3 cp --recursive s3://blah .`

Prerequisites
* pip3 install moviepy

That should be it.  Make sure you have ffmpeg installed, and imagemagick
* brew install ffmpeg
* brew install imagemagick

If you don't know brew, I can't help you
