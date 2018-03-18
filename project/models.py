from datetime import datetime
from random import randint
from hashlib import md5
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from project import db, login, celery
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    path = db.Column(db.String(4096))

    videos = db.relationship('Video', backref='directory', lazy='dynamic')

    def __repr__(self):
        return '<Directory {}>'.format(self.path)

    def has_active_videos(self):
        active = False
        for video in self.videos:
            if video.is_active():
                active = True
                break
        return active

    def get_active_videos(self):
        active_videos = []
        for video in self.videos:
            if video.is_active():
                active_videos.append(video)
        return active_videos

# Many to Many relationship between channels and videos.
# Add Video to Channel: Channel.videos.append(video_id)
# Add Channel to Video: Video.channels.append(channel_id) - Technically redundant.  Don't use.
chan_vid_relationship = db.Table('chan_vid_relationship',
                                 db.Column('channel_id',
                                           db.Integer,
                                           db.ForeignKey('channel.id'),
                                           nullable=False),
                                 db.Column('video_id',
                                           db.Integer,
                                           db.ForeignKey('video.id'),
                                           nullable=False),
                                 db.PrimaryKeyConstraint('channel_id',
                                                         'video_id'))

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(4096))
    first_seen = db.Column(db.DateTime, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())
    active = db.Column(db.Boolean, default=True)
    directory_id = db.Column(db.Integer, db.ForeignKey('directory.id'))

    def __repr__(self):
        return '<File {}>'.format(self.filepath)

    def serialize(self):
        dict = {}
        dict['id'] = self.id
        dict['filepath'] = self.filepath
        dict['first_seen'] = self.first_seen
        dict['last_seen'] = self.last_seen
        dict['active'] = self.active
        dict['directory_id'] = self.directory_id
        return dict

    def seen(self):
        self.last_seen = datetime.utcnow()

    def set_active(self, bool):
        self.active = bool

    def is_active(self):
        return self.active

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    serial = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    videos = db.relationship('Video', secondary=chan_vid_relationship, backref='channels')

    def __repr__(self):
        return '<Channel {}>'.format(self.id)

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_owner_username(self):
        return self.owner.username

    def set_name(self, s):
        self.name = s

    def has_active(self):
        active =  False
        for video in self.videos:
            if video.is_active():
                active = True
                break
        return active

    def active_video_count(self):
        count = 0
        for video in self.videos:
            if video.is_active():
                count += 1
        return count

    def total_video_count(self):
        #count = 0
        #for video in self.videos:
        #    count += 1
        #return count
        return len(self.videos)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), index=True, unique=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    channels = db.relationship('Channel', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint_id = db.Column(db.String(48), db.ForeignKey('endpoint.uuid'))
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<History {}>'.format(self.id)

class Endpoint(db.Model):
    uuid = db.Column(db.String(48), primary_key=True, index=True)
    key = db.Column(db.String(256))
    name = db.Column(db.String(64))                                             # Checkin value

    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())

    current_state = db.Column(db.String(32))                                    # Checkin value
    desired_state = db.Column(db.String(32))

    desired_channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))
    current_channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))     # Checkin value

    queued_video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    current_video_id = db.Column(db.Integer, db.ForeignKey('video.id'))         # Checkin value
    completed_video_id = db.Column(db.Integer, db.ForeignKey('video.id'))

    def __repr__(self):
        return '<Endpoint {}>'.format(self.uuid)

    def seen(self):
        self.last_seen = datetime.utcnow()

    def queue_check(self):
        queue_required = False

        # If there is no queued video, queue up a video.
        if self.get_queued_video() is None:
            print('Queue Check: No queued video. Queueing new video.')
            queue_required = True

        # If the video queued is also the video playing a video may need to be queued.
        if self.get_queued_video() == self.get_current_video():
            print('Queue Check: Queued video is playing. Attempting to queue a new video.')
            queue_required = True

        if queue_required:
            self.queue()

    def queue(self):
        # Create "active" list.
        # First query DB for channel data.
        channel = Channel.query.filter_by(id=self.get_desired_channel()).first()
        # Strip videos from the channel.
        channel_videos = [video for video in channel.videos]
        # Parse videos and pull out only the ones which are active.
        active_video_ids = []
        for video in channel_videos:
            if video.is_active():
                active_video_ids.append(video.id)

        # Create "exclusions" list.
        exclusions = []
        if len(active_video_ids) > 2:
            # If more than two videos exist, get the history and current video to build exclusions.
            # First query DB for history data  for this endpoint's last played videos in the current channel.
            history = History.query.filter_by(endpoint_id=self.get_uuid(), channel_id=self.get_desired_channel()) \
                .order_by(History.timestamp.desc()).limit(int(len(active_video_ids)*.8))
            # Strip relevant data from query results.
            exclusions = [h.video_id for h in history]
            # Also add the currently playing video.
            exclusions.append(self.get_current_video())
        elif len(active_video_ids) == 2:
            # If only 2 active videos exist in channel, the only exclusion is the current video
            # which leaves the only other video as a candidate
            exclusions.append(self.get_current_video())
        elif len(active_video_ids) == 1:
            # If  only 1 active video exists, then we must queue it by leaving exclusions list empty.
            pass

        # Create pool of videos to choose from.
        # Pool = Active - Exclusions
        pool = []
        for video in active_video_ids:
            if video not in exclusions:
                pool.append(video)

        # Pick a video randomly from the pool
        random_video_id = pool[randint(0, len(pool) - 1)]

        # Set the video to the endpoint's queue.
        self.set_queued_video(random_video_id)

    def checkin(self, state, name, channel, video):
        if self.get_name() != name:                 # Endpoint name
            self.set_name(name)
        if self.get_state() != state:               # Endpoint state
            if state == 'SKIP':
                self.set_desired_state('PLAY')
            self.set_state(state)
        if self.get_current_video() != video:       # Endpoint video (playing)
            self.set_current_video(video)
        if self.get_current_channel() != channel:   # Endpoint channel
            self.set_current_channel(channel)
        self.seen()

        # When new endpoints are added, they have no assigned/desired channel, so do nothing in that case.
        if self.get_desired_channel() is None:
            pass
        else:
            self.queue_check()

    def checkout(self):
        video = Video.query.filter_by(id=self.get_queued_video()).first()
        video_path = video.filepath

        dict = {'desired_state': self.get_desired_state(),
                'desired_channel': self.get_desired_channel(),
                'queued_video': self.get_queued_video(),
                'queued_video_path': video_path}
        return dict

    def get_last_seen(self):
        return self.last_seen

    def get_created_at(self):
        return self.created_at

    def set_queued_video(self, id):
        self.queued_video_id = int(id)

    def get_queued_video(self):
        return self.queued_video_id

    def set_current_video(self, v):
        if v is None:
            self.current_video_id = None
        else:
            self.current_video_id = int(v)

    def get_current_video(self):
        return self.current_video_id

    def set_desired_channel(self, c):
        self.desired_channel_id = c

    def get_desired_channel(self):
        return self.desired_channel_id

    def set_current_channel(self, c):
        self.current_channel_id = c

    def get_current_channel(self):
        if self.current_channel_id is None:
            return 0
        return int(self.current_channel_id)

    def get_uuid(self):
        return self.uuid

    def set_name(self, s):
        self.name = s

    def get_name(self):
        return self.name

    def set_state(self, s):
        self.current_state = s

    def get_state(self):
        return self.current_state

    def get_current_state(self):
        return self.current_state

    def set_desired_state(self, s):
        self.desired_state = s

    def get_desired_state(self):
        return self.desired_state

    def key_valid(self, k):
        if self.key == k:
            return True
        return False