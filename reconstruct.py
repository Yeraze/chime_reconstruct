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


def main():
    import os
    import json
    import datetime

    # Get all .txt files in the meeting-events directory
    path = os.path.join(os.getcwd(), "meeting-events")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".txt")]

    tsStart = None
    tsEnd = None
    events = []

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

                if data["EventType"] != "ActiveSpeaker":
                    date, time = parse_date(data["Timestamp"])
                    event = dict()
                    event["ts"] = (date, time)
                    event["type"] = data["EventType"]
                    events.append(event)

    # Now do the same for the data-channel
    path = os.path.join(os.getcwd(), "data-channel")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".txt")]
    dataChannel = []

    # Iterate over all .txt files
    for file in files:
        # Open the file
        with open(os.path.join(path, file), "r") as f:
            # iterate over every line in file f
            for line in f:
                # Parse the line as a JSON object
                data = json.loads(line)
            
                date, time = parse_date(data["Timestamp"])
                msg = dict()
                msg["ts"] = (date, time)
                msg["data"] = data["Data"]
                dataChannel.append(msg)

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

    print("Recording duration: %i:%02i (%s seconds)" % 
          (sDuration / 60, sDuration % 60, sDuration))


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
        print("[%i/%i] Offset: %s => Video %s           " % (vFiles.index(file), len(vFiles), offset, file), end="\r")
        
        video = VideoFileClip("%s/%s" % (path, file), audio = False)
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
        # We drop the first audio block.. it seems to always be corrupted
        if offset < 5.0:
            continue
        print("[%i/%i] Offset: %s => Audio %s           " % (aFiles.index(file), len(aFiles), offset, file), end="\r")

        audio = AudioFileClip("%s/%s" % (path, file))   
        #print(" => Duration is %s" % audio.duration)
        aDuration = aDuration + audio.duration
        audio = audio.set_start(offset)
        audio = audio.set_duration(audio.duration)
        aClips.append(audio)


    print("Generating event labels...")
    eClips = []
    for e in events:
        clip = TextClip(e["type"], fontsize=60, color='white' )
        date, time = e["ts"]
        dt = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2])
        offset = (dt - dtStart).seconds
        clip = clip.set_start(offset)
        clip = clip.set_duration(1)
        clip = clip.set_pos(("left", "top"))
        eClips.append(clip)

    print("Generating data message...")
    # Just add these to the eClips
    for e in dataChannel:
        clip = TextClip(e["data"], fontsize=40, color='green' )
        date, time = e["ts"]
        dt = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2])
        offset = (dt - dtStart).seconds
        clip = clip.set_start(offset)
        clip = clip.set_duration(2)
        clip = clip.set_pos(("left", "bottom"))
        eClips.append(clip)       


    print("Preparing event comp:")
    CompEvents = CompositeVideoClip(eClips)
    CompEvents = CompEvents.set_duration(sDuration)

    print("Recording duration: %i:%02i (%s seconds)" % 
          (sDuration / 60, sDuration % 60, sDuration))
    print("Preparing audio comp: %s seconds (%i %% Coverage)" % (aDuration, 100.0 * aDuration / sDuration))
    CompAudio = CompositeAudioClip(aClips)
    CompAudio = CompAudio.set_duration(sDuration)
    print("Preparing video comp: %s seconds (%i %% Coverage)" % (vDuration, 100.0 * vDuration / sDuration))
    vClips.extend(eClips)
    CompVideo = CompositeVideoClip(vClips)
    CompVideo = CompVideo.set_duration(sDuration)
    CompVideo.audio = CompAudio

    print("Writing to output.mp4")
    CompVideo.write_videofile("output.mp4", fps=15, audio_codec='aac', threads=16, codec='libx264')
    print("Done!")







main()

            


