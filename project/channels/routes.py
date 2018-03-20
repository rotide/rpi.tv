from flask import jsonify
from project.channels import bp
from project.channels.modules import channel_to_dict
from project.models import Channel

@bp.route('/', methods=['GET'])
@bp.route('/all', methods=['GET'])
def all():
    channels = Channel.query.all()

    channels_dict = {}
    for channel in channels:
        channels_dict[channel.id] = channel_to_dict(channel)

    return jsonify({'channels':channels_dict})

@bp.route('/<channel_id>', methods=['GET'])
def channel(channel_id):
    channel = Channel.query.filter_by(id=channel_id).first()

    if channel != None:
        return jsonify({'channel':channel_to_dict(channel)})
    return '', 204

@bp.route('/<channel_id>/videos', methods=['GET'])
def channel_videos(channel_id):
    channel = Channel.query.filter_by(id=channel_id).first()

    if channel != None:
        #channel_json = jsonify({'channel':channel_to_dict(channel)})
        channel_json = {'channel': channel_to_dict(channel)}
        channel_videos = [video.id for video in channel.videos]
        print(channel_json.keys())
        channel_json['channel'].update({'videos': channel_videos})

        return jsonify(channel_json)
    return '', 204
