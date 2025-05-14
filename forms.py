from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class UploadForm(FlaskForm):
    """Form for uploading new images"""
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    category = SelectField('Category', choices=[
        ('Builds', 'Builds'),
        ('Landscapes', 'Landscapes'),
        ('Servers', 'Servers'),
        ('Redstone', 'Redstone'),
        ('Survival', 'Survival'),
        ('Creative', 'Creative'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    uploader = StringField('Your Name', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Upload')

class CommentForm(FlaskForm):
    """Form for adding comments to images"""
    username = StringField('Your Name', validators=[DataRequired(), Length(min=3, max=50)])
    text = TextAreaField('Comment', validators=[DataRequired(), Length(min=3, max=500)])
    submit = SubmitField('Post Comment')
