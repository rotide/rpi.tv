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
