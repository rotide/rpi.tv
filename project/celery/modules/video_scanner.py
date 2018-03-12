from datetime import datetime
from project import db, app, Config
from project.models import Video, Directory
import os

def scan():
    #app = create_app()

    folder = Config.VIDEO_BASE_DIR
    videxts = ['.mkv', '.mpg', '.avi', '.mp4']

    # Find all relevant media files and directories
    discovered_videos = []
    discovered_directories = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            # Split off the file extension
            ext = os.path.splitext(file)[1]
            # Compare extension with known video extensions.
            if ext.lower() in videxts:
                filepath = os.path.join(root, file)
                if filepath not in discovered_videos:
                    discovered_videos.append(filepath)
                if root not in discovered_directories:
                    discovered_directories.append(root)

    with app.app_context():
        # Get all existing directories from database.
        query_directories = Directory.query.all()
        existing_directories = []
        for directory in query_directories:
            existing_directories.append(directory.path)

        # Add new directories.
        for path in discovered_directories:
            if path not in existing_directories:
                directory = Directory(path=path)
                db.session.add(directory)

        # Commit directories.
        db.session.commit()

        # Get all existing media from database.
        query_videos = Video.query.all()

        # Determine which items in database were and were not found (active)
        existing_videos = []
        for video in query_videos:
            existing_videos.append(video.filepath)
            if video.filepath in discovered_videos:
                video.set_active(True)
            else:
                video.set_active(False)
            video.seen()

        # Determine which discovered files are NEW
        for filepath in discovered_videos:
            if filepath not in existing_videos:
                dir_path = os.path.dirname(filepath)
                directory = Directory.query.filter_by(path=dir_path).first()
                if directory != None:
                    video = Video(filepath=filepath, directory_id=directory.id)
                    db.session.add(video)

        # Commit changes to the database
        # Note: If ANY error is encountered, commit will NOT execute
        db.session.commit()
