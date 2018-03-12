from os import urandom
from base64 import b64encode

def endpoint_to_dict(e):
    d = {}
    d['uuid'] = e.get_uuid()
    d['last_seen'] = e.get_last_seen()
    d['current_state'] = e.get_current_state()
    d['desired_state'] = e.get_desired_state()
    d['created_at'] = e.get_created_at()
    d['name'] = e.get_name()
    d['current_channel'] = e.get_current_channel()
    d['current_video'] = e.get_current_video()
    d['desired_channel'] = e.get_desired_channel()
    d['queued_video'] = e.get_queued_video()
    return d

def get_rand_key():
    key = b64encode(urandom(64)).decode()
    return key
