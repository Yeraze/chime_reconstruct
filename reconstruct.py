import os
from moviepy.editor import *

# Parse string like "2023-11-11T12:04:15.262+00:00" into relevant date components as a tuple of individual integers
# Input: date_string (string)
# Output: date (tuple of integers), time (tuple of integers)
def parse_date(date_string):
    date = date_string.split("T")[0]
    time = date_string.split("T")[1].split(".")[0]
    date = tuple([int(x) for x in date.split("-")])
    time = tuple([int(x) for x in time.split(":")])
    return date, time

# Parse string like "2023-11-11-12-04-15-262-otherstuff" into relevant date components as a tuple of individual integers
# Input: date_string (string)
# Output: date (tuple of integers), time (tuple of integers)
def parse_date2(date_string):
    date_string = date_string.split(".")[0]
    date = date_string.split("-")[0:3]
    time = date_string.split("-")[3:6]
    ms   = date_string.split("-")[6]
    date = tuple([int(x) for x in date])
    time = tuple([int(x) for x in time])
    ms = int(ms)
    return date, time, ms


# Iterate over all .txt files in the meeting-events directory
# Input: None
# Output: None
def main():
    import os
    import json
    import datetime

    # Get all .txt files in the meeting-events directory
    path = os.path.join(os.getcwd(), "meeting-events")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".txt")]

    tsStart = None
    tsEnd = None

    # Iterate over all .txt files
    for file in files:
        # Open the file
        with open(os.path.join(path, file), "r") as f:
            # iterate over every line in file f
            for line in f:
                # Parse the line as a JSON object
                data = json.loads(line)
                if data["EventType"] == "CaptureStarted":
                    # Get the date and time of the meeting
                    date, time = parse_date(data["Timestamp"])
                    print("Found start")
                    tsStart = (date, time)
                if data["EventType"] == "CaptureEnded":
                    date, time = parse_date(data["Timestamp"])
                    print("Found End")
                    tsEnd = (date, time)


    print("Recording started at %s %s" % (tsStart[0], tsStart[1]))

    print("Recording stopped at %s %s" % (tsEnd[0], tsEnd[1]))

    # Calculcate the difference between tsStart and tsEnd in seconds
    # Convert the date and time tuples into datetime objects
    # Calculate the difference between the two datetime objects
    # Convert the difference into seconds
    # Print the difference
    dtStart = datetime.datetime(tsStart[0][0], tsStart[0][1], tsStart[0][2], tsStart[1][0], tsStart[1][1], tsStart[1][2])
    dtEnd = datetime.datetime(tsEnd[0][0], tsEnd[0][1], tsEnd[0][2], tsEnd[1][0], tsEnd[1][1], tsEnd[1][2])
    diff = dtEnd - dtStart
    sDuration = diff.seconds

    print("Recording duration: %s seconds" % sDuration)


    # Start compositing all the bits and bobs
    # Start with the video
    vClips = []
    path = os.path.join(os.getcwd(), "video")
    vFiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".mp4")]
    vDuration = 0
    for file in vFiles:
        # Start by retreiving the timestamp so we know where this video clip goes
        date, time, ms = parse_date2(file)
        dt = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2])
        offset = (dt - dtStart).seconds + ms/1000.0
        print("Offset: %s => Video %s" % (offset, file))
        
        video = VideoFileClip("%s/%s" % (path, file), audio = False, target_resolution = (720, 1280))
        #print(" => Duration is %s" % video.duration)

        vDuration = vDuration + video.duration
        video = video.set_start(offset)
        video = video.set_duration(video.duration)
        vClips.append(video)

    # move on to audio
    aClips = []
    path = os.path.join(os.getcwd(), "audio")
    aFiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".mp4")]
    aDuration = 0
    for file in aFiles:
        # Start by retreiving the timestamp so we know where this video clip goes
        date, time, ms = parse_date2(file)
        dt = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2])
        offset = (dt - dtStart).seconds + ms/1000.0
        print("Offset: %s => Audio %s" % (offset, file))

        audio = AudioFileClip("%s/%s" % (path, file))   
        #print(" => Duration is %s" % audio.duration)
        aDuration = aDuration + audio.duration
        audio = audio.set_start(offset)
        audio = audio.set_duration(audio.duration)
        aClips.append(audio)


    print("Preparing audio comp: %s seconds" % aDuration)
    CompAudio = CompositeAudioClip(aClips)
    CompAudio = CompAudio.set_duration(sDuration)
    print("Preparing video comp: %s seconds" % vDuration)
    CompVideo = CompositeVideoClip(vClips)
    CompVideo = CompVideo.set_duration(sDuration)


    CompVideo.audio = CompAudio
    print("Writing to output.mp4")
    CompVideo = CompVideo.write_videofile("output.mp4", fps=24, audio_codec='aac', threads=8, codec='libx264')
    print("Done!")







main()

            


