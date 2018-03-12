from project import db, app, Config
from project.models import Endpoint, History, Channel

def queue(e):
    channel = Channel.query.filter_by(id=e.get_desired_channel()).first()
    print('Channel: ' + channel.get_name())
    #print(channel.videos)
    videos = [item.filepath for item in channel.videos]
    for video in videos:
        print(video)