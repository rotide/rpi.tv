import os
from flask import request, render_template, jsonify
from project import db, celery
from project.models import Video, Directory
from project.videos import bp
from project.celery.tasks import video_scanner

@bp.route('/scan', methods=['POST'])
def scan():
    video_scanner.apply_async()
    return jsonify({"message":"Scan Initiated"}), 202

@bp.route('/', methods=['GET'])
@bp.route('/all', methods=['GET'])
def all():
    videos = Video.query.all()

    videos_json = {}
    for video in videos:
        #video_json = {'folder_path':f.directory.path,
        #        'folder_id':f.directory_id,
        #        'active':f.active,
        #        'id':f.id,
        #        'filepath':f.filepath,
        #        'first_seen':f.first_seen,
        #        'last_seen':f.last_seen}
        videos_json.update({video.id:video.serialize()})

    return jsonify({'videos':videos_json})

@bp.route('/<video_id>', methods=['GET'])
def video(video_id):
    video = Video.query.filter_by(id=video_id).first()

    video_json = {}
    if video is not None:
        video_json = video.serialize()
    return jsonify({'video': video_json})

@bp.route('/dirs', methods=['GET'])
def dirs():
    results = Directory.query.all()

    dirs = {}
    for d in results:
        dirs[d.path] = []
        for v in d.videos:
            dirs[d.path].append(os.path.basename(v.filepath))
        dirs[d.path].sort()

    return jsonify({'directories':dirs})
