import os
from uuid import uuid4
from flask import request, render_template, jsonify
from project import db, celery
from project.models import Endpoint, History
from project.endpoint import bp
from project.endpoint.modules import endpoint_to_dict, get_rand_key

@bp.route('/', methods=['GET'])
@bp.route('/all', methods=['GET'])
def all():
    endpoints = Endpoint.query.all()

    ep_dict = {}
    for endpoint in endpoints:
        ep_dict[endpoint.get_uuid()] = endpoint_to_dict(endpoint)

    return jsonify({'endpoints':ep_dict})

@bp.route('/register', methods=['POST'])
def register():
    uuid = str(uuid4())
    key = get_rand_key()
    endpoint = Endpoint(uuid=uuid, key=key)
    db.session.add(endpoint)
    db.session.commit()
    return jsonify({"uuid":uuid, "key":key}), 202

@bp.route('/<uuid>', methods=['GET'])
def endpoint(uuid):
    endpoint = Endpoint.query.filter_by(uuid=uuid).first()

    if endpoint != None:
        ep_dict = endpoint_to_dict(endpoint)
        return jsonify({'endpoint': ep_dict})
    return '', 204

@bp.route('/desiredstate/<uuid>', methods=['GET'])
def desiredstate(uuid):
    endpoint = Endpoint.query.filter_by(uuid=uuid).first()
    if endpoint != None:
        return jsonify({'desired_state': endpoint.desired_state})
    return '', 204

@bp.route('/checkin', methods=['POST'])
def checkin():
    if not request.data or not request.is_json:
        return jsonify({'error':'missing required data or request not json'}), 406

    data = request.get_json()

    required_keys = ['uuid', 'key', 'state', 'name', 'channel', 'video', 'completed_video']
    keys_found = True
    for r in required_keys:
        if r not in data.keys():
            keys_found = False
    if not keys_found:
        return jsonify({'error':'missing required data'}), 406

    uuid = data['uuid']
    key = data['key']
    state = data['state']
    name = data['name']
    channel = data['channel']
    video = data['video']
    completed_video = data['completed_video']

    endpoint = Endpoint.query.filter_by(uuid=uuid, key=key).first()
    if endpoint == None:
        return jsonify({'error':'invalid uuid or key'}), 406

    if completed_video is not None:
        history = History(endpoint_id=uuid, video_id=completed_video, channel_id=channel)
        db.session.add(history)

    endpoint.checkin(state, name, channel, video)

    db.session.commit()
    return '', 202

@bp.route('/checkout/<uuid>', methods=['GET'])
def checkout(uuid):
    endpoint = Endpoint.query.filter_by(uuid=uuid).first()
    if endpoint != None:
        return jsonify({endpoint.get_uuid():endpoint.checkout()}), 200
    return '', 204

@bp.route('/checkout/all', methods=['GET'])
def checkout_all():
    endpoints = Endpoint.query.all()
    dict = {}
    for endpoint in endpoints:
        sub_dict = {'desired_channel': endpoint.get_desired_channel(),
                    'desired_state': endpoint.get_desired_state(),
                    'queued_video': endpoint.get_queued_video()}
        dict.update({endpoint.get_uuid(): sub_dict})
    return jsonify({'endpoints': dict}), 200

@bp.route('/playing_use_checkin_instead', methods=['POST'])
def playing():
    if not request.data or not request.is_json:
        return jsonify({'error':'missing required data or request not json'}), 406

    data = request.get_json()
    required_keys = ['uuid', 'key', 'video']
    for k in required_keys:
        if k not in data.keys():
            return jsonify({'error':'missing required data'}), 406

    uuid = data['uuid']
    key = data['key']
    video = data['video']

    endpoint = Endpoint.query.filter_by(uuid=uuid, key=key).first()
    if endpoint == None:
        return jsonify({'error':'invalid uuid or key'})

    endpoint.playing(video)
    # GET NEXT VIDEO - SET NEXT VIDEO

    db.session.commit()
    return '', 202

# Notify server video completed.
@bp.route('/played', methods=['POST'])
@bp.route('/videoend', methods=['POST'])
def played():
    if not request.data or not request.is_json:
        return jsonify({'error':'missing data: {uuid, key, video} or request not json'}), 406

    data = request.get_json()
    required_keys = ['uuid', 'key', 'video', 'channel']
    for k in required_keys:
        if k not in data.keys():
            return jsonify({'error':'missing required data'}), 406

    uuid = data['uuid']
    key = data['key']
    video = data['video']
    channel = data['channel']

    endpoint = Endpoint.query.filter_by(uuid=uuid, key=key).first()
    if endpoint == None:
        return jsonify({'error':'invalid uuid or key'})

    endpoint.set_current_video(None)
    endpoint.set_state('STOPPED')

    db.session.commit()
    return '',202
