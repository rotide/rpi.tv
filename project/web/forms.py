from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError
from project.models import Channel
from sqlalchemy import func

class ControllerOLDForm(FlaskForm):
    play = SubmitField(label='Play')
    pause = SubmitField(label='Pause')
    stop = SubmitField(label='Stop')
    skip = SubmitField(label='Skip')

#    endpoint = BooleanField('Endpoint')

class ControllerForm(FlaskForm):
    # Placeholder
    pass

class ScanForm(FlaskForm):
    scan = SubmitField(label='Scan')

class ChannelCreateForm(FlaskForm):
    name = StringField('Channel Name', validators=[DataRequired()])
    serial = BooleanField('Serial')
    submit = SubmitField(label='Create')

    #def validate_name(self, name):
    #    channel = Channel.query.filter(func.lower(Channel.name)==func.lower(name.data)).first()
    #    if channel != None:
    #        raise ValidationError('Channel name already in use. Please user another.')

class ChannelEditForm(FlaskForm):
    submit = SubmitField(label='Delete')