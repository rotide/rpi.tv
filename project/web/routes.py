import os
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

    active = db.session.execute(db.session.query(Video).filter_by(active=True).statement.with_only_columns([func.count()]).order_by(None)).scalar()
    inactive = db.session.execute(db.session.query(Video).filter_by(active=False).statement.with_only_columns([func.count()]).order_by(None)).scalar()

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
                    filename = os.path.basename(video.filepath)
                    dict[directory.path].append([video.id, filename])
            dict[directory.path].sort(key=lambda x: x[1])

    if form.validate_on_submit():
        channel = Channel(name=form.name.data, user_id=current_user.id)

        #videos = Video.query.all()
        videos = Video.query.filter_by(active=True)
        video_count = 0
        for video in videos:
            if 'checked' in request.form.getlist(str(video.id)):
                # While the model explicitly states video.id is stored, we pass the video object.
                channel.videos.append(video)
                video_count += 1

        try:
            db.session.add(channel)
            db.session.commit()
            flash('Channel ' + form.name.data + ' with ' + str(video_count) + ' videos created successfully.')
        except:
            flash('Channel creation encountered an error during database operation.')

        return redirect(url_for('web.channel_create'))
    return render_template('web/channel_create.html', form=form, dirs=dict)

@bp.route('/channeleditorold', methods=['GET', 'POST'])
@login_required
def channel_edit_old():
    form = ChannelEditForm()

    if form.validate_on_submit():
        for item in request.form:
            print(item)

        # If a radio button was selected
        #if 'options' in request.form:
        #    selected = request.form['options']

        # If the DELETE button was pressed.
        for form_item in request.form:
            if 'button-' in form_item:
                # Get action associated with button press
                button_action = form_item.split('-')[1]
                # Get channel associated with button press
                button_channel = form_item.split('-')[2]

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

                elif button_action == 'rename':
                    rename_to = request.form['text-rename-' + str(button_channel)]
                    if rename_to.strip() is not '':
                        # Get channel from database.
                        channel = Channel.query.filter_by(id=button_channel, user_id=current_user.id).first()
                        # Get channel's name for alerting purposes.
                        rename_from = channel.name
                        # Set channel's new name.
                        channel.set_name(rename_to)
                        # Commit database changes.
                        db.session.commit()
                        flash('Channel renamed from "' + rename_from + '" to "' + rename_to + '".')

    channels = Channel.query.filter_by(user_id=current_user.id)
    channels_array = []
    for channel in channels:
        c = {}
        c.update({'id':channel.id})
        c.update({'name':channel.name})
        c.update({'total_videos':channel.total_video_count()})
        c.update({'active_videos':channel.active_video_count()})
        channels_array.append(c)

    return render_template('web/channel_edit.html', form=form, channels=channels_array)

@bp.route('/channeledit', methods=['GET', 'POST'])
@login_required
def channel_edit():
    form = ChannelEditForm()

    # Initialize variables which will be passed to render_template.
    selected_channel = None
    channel_videos = {}

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

        # Pull channel/video information from database for web page rendering if a channel was selected.
        if selected_channel:
            # Get data for selected channel ID.
            channel = Channel.query.filter_by(id=selected_channel).first()

            if channel is not None:
                # Generate array of video information from selected channel data
                video_array = [
                    [os.path.dirname(video.filepath),   # Video Directory
                     video.id,                          # Video ID
                     os.path.basename(video.filepath),  # Video Filename
                     video.active]                      # Active (bool)
                    for video in channel.videos
                ]

                for video in video_array:
                    # If video directory not already in channel_videos...
                    if video[0] not in channel_videos.keys():
                        # Create directory key in dict.
                        channel_videos[video[0]] = []
                    # Append video data to dict key (folder).
                    channel_videos[video[0]].append([video[1], video[2], video[3]])

                # Sort each set of videos for each directory.
                for directory in channel_videos.keys():
                    channel_videos[directory].sort(key=lambda x: x[1])

#    # Gather all Channels owned by the user.
#    channels = Channel.query.filter_by(user_id=current_user.id).all()

#    # Generate channel list which will be displayed to the user for channel selection.
#    channels_array = []
#    for channel in channels:
#        channels_array.append([channel.id,
#                               channel.name,
#                               channel.owner.username])

    channels = Channel.query.filter_by(user_id=current_user.id).all()
    channels_array = []
    for channel in channels:
        c = {}
        c.update({'id': channel.get_id()})
        c.update({'name': channel.get_name()})
        c.update({'owner': channel.get_owner_username()})
        c.update({'total_videos': channel.total_video_count()})
        c.update({'active_videos': channel.active_video_count()})
        channels_array.append(c)


    return render_template('web/channel_edit.html', channels=channels_array, form=form,
                           selected_channel=selected_channel, videos=channel_videos)

@bp.route('/controller', methods=['GET', 'POST'])
@login_required
def controller():
    form = ControllerForm()

    # Endpoint(s) must check in within this timeframe to be considered active.
    endpoint_expiry_seconds = 60

    endpoints = Endpoint.query.all()
    channels = Channel.query.all()

    active_endpoints = []
    array_endpoints = []
    now = datetime.utcnow()
    for endpoint in endpoints:
        if now > endpoint.last_seen:
            delta_s = (now - endpoint.last_seen).seconds
        else:
            delta_s = 0

        if delta_s < endpoint_expiry_seconds:
            active_endpoints.append(endpoint)
            array_endpoints.append([endpoint.uuid,
                                    endpoint.name,
                                    endpoint.current_state,
                                    endpoint.queued_video_id])

    array_channels = []
    for channel in channels:
        if channel.has_active():
            array_channels.append([channel.id,
                                   channel.name,
                                   channel.owner.username])

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

    return render_template('web/controller.html', form=form, endpoints=array_endpoints, channels=array_channels)
