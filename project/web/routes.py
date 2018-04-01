from datetime import datetime
from flask import request, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from project import db, celery
from project.models import Video, Endpoint, Directory, Channel, History
from project.web import bp
from project.web.forms import ControllerForm, ScanForm, ChannelCreateForm, ChannelEditForm
from project.celery.tasks import video_scanner
from sqlalchemy import func

@bp.route('/', methods=['GET'])
def index():
    # Basic Statistics
    # Number of active videos
    # Number of inactive videos
    # Last video scan
    # Total Endpoints
    # Active Endpoints
    return render_template('web/index.html')

@bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    form = ScanForm()

    active = db.session.execute(db.session.query(Video).filter_by(active=True)
                                .statement.with_only_columns([func.count()]).order_by(None)).scalar()
    inactive = db.session.execute(db.session.query(Video).filter_by(active=False)
                                  .statement.with_only_columns([func.count()]).order_by(None)).scalar()

    if form.scan.data:
        video_scanner.apply_async()
        flash("Scan Initiated - Refresh this page in a few seconds to update totals")
        # REDIRECT back to the same page.
        # This stops the confirmation for resubmitting form data.
        return redirect(url_for('web.scan'))

    return render_template('web/scan.html', form=form, active=active, inactive=inactive)

@bp.route('/channelcreate', methods=['GET', 'POST'])
@login_required
def channel_create():
    form = ChannelCreateForm()

    directories = Directory.query.all()
    dict = {}
    for directory in directories:
        if directory.has_active_videos():
            dict[directory.path] = []
            for video in directory.videos:
                if video.is_active():
                    filename = video.get_filename()
                    dict[directory.path].append([video.id, filename])
            dict[directory.path].sort(key=lambda x: x[1])

    if form.validate_on_submit():
        channel = Channel(name=form.name.data, user_id=current_user.id)

        if 'file' in request.form.keys():
            selected_video_ids = request.form.getlist('file')

            for id in selected_video_ids:
                video = Video.query.filter_by(active=True, id=id).first()
                if video is not None:
                    channel.videos.append(video)

            try:
                db.session.add(channel)
                db.session.commit()
                flash('Channel ' + str(channel.get_name()) + ' with ' + str(channel.total_video_count()) + ' videos created successfully.')
            except:
                flash('Channel creation encountered an error during database operation.')
        else:
            flash('No videos selected. Channel creation aborted.')

        return redirect(url_for('web.channel_create'))
    return render_template('web/channel_create.html', form=form, dirs=dict)

@bp.route('/channeledit', methods=['GET', 'POST'])
@login_required
def channel_edit():
    form = ChannelEditForm()

    # Initialize variables which will be passed to render_template.
    selected_channel = None
    channel_videos_dict = {}
    available_videos_dict = {}
    available_videos_list = []

    if form.validate_on_submit():
        print(request.form)

        # If user selected a channel, get the channel ID from form data.
        if request.form['select']:
            selected_channel = request.form['select']
        else:
            selected_channel = None

        # Determine which form button was pressed and get the channel id associated with it (if applicable).
        button_action = None
        button_channel = None
        for form_item in request.form:
            if 'button-' in form_item:
                button_array = form_item.split('-')
                button_action = button_array[1].lower()
                if len(button_array) == 3:
                    button_channel = button_array[2]

        print('BUTTON ACTION : ' + str(button_action))
        print('BUTTON CHANNEL: ' + str(button_channel))

        if button_action == 'delete':
            # Get channel data and verify it's for the current user (input validation and authorization)
            channel = Channel.query.filter_by(id=button_channel, user_id=current_user.id).first()

            # Get any endpoints which may be currently set to the channel to be deleted.
            endpoint = Endpoint.query.filter_by(current_channel_id=button_channel).first()
            if endpoint is not None:
                # An endpoint is tuned in to the channel to be deleted, notify user.
                flash('An endpoint is set to your selected channel.  It can not be deleted at this time.')
            else:
                if channel is not None:
                    # Clear channel's history from database.
                    for history in History.query.filter_by(channel_id=button_channel).all():
                        db.session.delete(history)
                    # Clear channel from database.
                    db.session.delete(channel)
                    # Commit database changes.
                    db.session.commit()
                    flash('Channel deleted: ' + str(channel.name))

                    # User selected channel has been deleted so we must unset the selected channel.
                    selected_channel = None

        elif button_action == 'rename':
            print('BUTTON: RENAME')
            rename_to = request.form['text-rename-' + str(button_channel)]
            print("RenameTo: " + rename_to)
            if rename_to.strip() is not '':
                # Get channel from database.
                channel = Channel.query.filter_by(id=button_channel, user_id=current_user.id).first()
                if channel is not None:
                    # Get channel's name for alerting purposes.
                    rename_from = channel.name
                    # Set channel's new name.
                    channel.set_name(rename_to)
                    # Commit database changes.
                    db.session.commit()
                    flash('Channel renamed from "' + rename_from + '" to "' + rename_to + '".')

        elif button_action == 'add':
            print('BUTTON: ADD')
            print('ADD: ' + str(request.form.getlist('file-add')))
            channel = Channel.query.filter_by(id=button_channel, user_id=current_user.id).first()
            if channel is not None:
                for video_id in request.form.getlist('file-add'):
                    video = Video.query.filter_by(id=video_id, active=True).first()
                    if video is not None:
                        channel.videos.append(video)
                db.session.commit()
                flash('Videos added to channel successfully.')

        elif button_action == 'remove':
            print('BUTTON: REMOVE')
            print('REMOVE: ' + str(request.form.getlist('file-rem')))
            channel = Channel.query.filter_by(id=button_channel, user_id=current_user.id).first()
            if channel is not None:
                for video_id in request.form.getlist('file-rem'):
                    video = Video.query.filter_by(id=video_id, active=True).first()
                    if video is not None:
                        channel.videos.remove(video)
                db.session.commit()
                flash('Videos removed from channel successfully.')

        # Pull channel/video information from database for web page rendering if a channel was selected.
        if selected_channel:
            # Get data for selected channel ID.
            channel = Channel.query.filter_by(id=selected_channel).first()

            if channel is not None:
                # Generate array of video information from selected channel data
                video_array = [
                    [video.get_directory_path(),    # Video Directory
                     video.get_id(),                # Video ID
                     video.get_filename(),          # Video Filename
                     video.is_active()]             # Active (bool)
                    for video in channel.videos
                ]

                for video in video_array:
                    # If video directory not already in channel_videos...
                    if video[0] not in channel_videos_dict.keys():
                        # Create directory key in dict.
                        channel_videos_dict[video[0]] = []
                    # Append video data to dict key (folder).
                    channel_videos_dict[video[0]].append([video[1], video[2], video[3]])

                # Sort each set of videos for each directory.
                for directory in channel_videos_dict.keys():
                    channel_videos_dict[directory].sort(key=lambda x: x[1])

                # Get all other videos to preset to user to ADD to channel
                directories = Directory.query.all()
                if directories is not None:
                    #for directory in directories:
                    #    video_dict = {}
                    #    for video in directory.get_active_videos():
                    #        video_dict[video.get_filename()] = {'id': video.get_id(),
                    #                                            'filename': video.get_filename()}

                    #    available_videos_dict[directory.get_path()] = {'directory': directory.get_path()}
                    #    available_videos_dict[directory.get_path()].update({'videos': video_dict})

                    for directory in directories:
                        # Only parse directory if it has active videos.
                        if directory.has_active_videos():
                            # Get/Put every active video in the directory into a list.
                            directory_videos = []
                            for v in directory.get_active_videos():
                                # Each Video will consist of the video ID and the Filename.
                                video = [v.get_id(), v.get_filename()]
                                # Add Video to list directory_videos.
                                directory_videos.append(video)
                            # Sort directory_videos by Video Filename (ignore case).
                            directory_videos = sorted(directory_videos, key=lambda video: video[1].lower())
                            # Add the Directory and its Videos to the available_videos_list.
                            available_videos_list.append([directory.get_path(),directory_videos])
                    # Sort available_videos_list by Directory Path (ignore case).
                    available_videos_list = sorted(available_videos_list, key=lambda directory: directory[0].lower())

    # Gather all Channels owned by the user.
    channels = Channel.query.filter_by(user_id=current_user.id).all()

    channels_list = []
    if channels is not None:
        for channel in channels:
            c = []
            c.append(channel.get_id())
            c.append(channel.get_name())
            c.append(channel.get_owner_username())
            c.append(channel.total_video_count())
            c.append(channel.active_video_count())
            channels_list.append(c)
        channels_list = sorted(channels_list, key=lambda c: c[1].lower())

    return render_template('web/channel_edit.html',
                           channels=channels_list,
                           form=form,
                           selected_channel=selected_channel,
                           channel_videos=channel_videos_dict,
                           available_videos=available_videos_list)

@bp.route('/controller', methods=['GET', 'POST'])
@login_required
def controller():
    form = ControllerForm()

    # Endpoint(s) must check in within this timeframe to be considered active.
    endpoint_expiry_seconds = 60

    endpoints = Endpoint.query.all()
    channels = Channel.query.all()

    active_endpoints = []
    endpoints_dict = {}
    now = datetime.utcnow()
    for endpoint in endpoints:
        if now > endpoint.last_seen:
            delta_s = (now - endpoint.last_seen).seconds
        else:
            delta_s = 0

        if delta_s < endpoint_expiry_seconds:
            current_video = Video.query.filter_by(id=endpoint.get_current_video()).first()
            next_video = Video.query.filter_by(id=endpoint.get_queued_video()).first()

            active_endpoints.append(endpoint)
            e = {}
            e['uuid'] = endpoint.get_uuid()
            e['name'] = endpoint.get_name()
            e['current_state'] = endpoint.get_current_state()
            e['queued_video'] = endpoint.get_queued_video()
            e['current_channel'] = endpoint.get_current_channel()
            e['current_video_filename'] = current_video.get_filename()
            e['next_video_filename'] = next_video.get_filename()
            endpoints_dict['endpoint.get_uuid()'] = e

    channels_dict = {}
    for channel in channels:
        if channel.has_active():
            c = {}
            c['id'] = channel.get_id()
            c['name'] = channel.get_name()
            c['owner'] = channel.get_owner_username()
            channels_dict[channel.get_id()] = c

    if form.validate_on_submit():
        for endpoint in active_endpoints:
            str_play = 'play-' + str(endpoint.get_uuid())
            str_pause = 'pause-' + str(endpoint.get_uuid())
            str_skip = 'skip-' + str(endpoint.get_uuid())
            str_stop = 'stop-' + str(endpoint.get_uuid())
            str_chan = 'chan-' + str(endpoint.get_uuid())
            str_select = 'select-' + str(endpoint.get_uuid())

            desired_state = None
            if str_play in request.form:
                desired_state = 'PLAY'
            elif str_pause in request.form:
                desired_state = 'PAUSE'
            elif str_stop in request.form:
                desired_state = 'STOP'
            elif str_skip in request.form:
                desired_state = 'SKIP'

            # Check for channel set request.  If found, set channel.
            if str_chan in request.form:
                chan_set = request.form[str_select]
                if int(chan_set) != endpoint.get_desired_channel():
                    try:
                        endpoint.set_desired_channel(chan_set)
                        endpoint.queue()
                        db.session.commit()
                        channel = Channel.query.filter_by(id=chan_set).first()
                        if channel is not None:
                            flash(endpoint.get_name() + ' channel changed to ' + str(channel.name) + '.')
                    except Exception as e:
                        flash('Error: %s' % str(e))

            if desired_state is not None:
                try:
                    endpoint.set_desired_state(desired_state)
                    db.session.commit()
                    flash(endpoint.get_name() + ' set to ' + desired_state)
                    return redirect(url_for('web.controller'))
                except Exception as e:
                    flash('Error: %s' % str(e))

    return render_template('web/controller.html', form=form, endpoints=endpoints_dict, channels=channels_dict)
