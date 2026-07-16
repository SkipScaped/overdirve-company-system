from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, BooleanField, EmailField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered.')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    profile_pic = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

# ─── Legacy forms kept for compatibility ──────────────────────────────────────
class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    category = SelectField('Category', choices=[
        ('General', 'General'), ('Other', 'Other')
    ], validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')])
    uploader = StringField('Your Name', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Upload')

class CommentForm(FlaskForm):
    username = StringField('Your Name', validators=[DataRequired(), Length(min=3, max=50)])
    text = TextAreaField('Comment', validators=[DataRequired(), Length(min=3, max=500)])
    submit = SubmitField('Post Comment')

# ─── Company Management Forms ─────────────────────────────────────────────────

class CompanyUpdateForm(FlaskForm):
    title    = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    content  = TextAreaField('Content', validators=[DataRequired(), Length(min=10)])
    category = SelectField('Category', choices=[
        ('General', 'General'),
        ('Development', 'Development'),
        ('Design', 'Design'),
        ('Marketing', 'Marketing'),
        ('Operations', 'Operations'),
        ('HR', 'HR'),
        ('Finance', 'Finance'),
        ('Announcement', 'Announcement'),
    ])
    is_pinned = BooleanField('Pin this update')
    submit   = SubmitField('Post Update')

class ExpenseProposalForm(FlaskForm):
    title       = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description / Justification', validators=[DataRequired(), Length(min=10)])
    amount      = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    currency    = SelectField('Currency', choices=[('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR'), ('CAD', 'CAD')])
    category    = SelectField('Category', choices=[
        ('General', 'General'),
        ('Software', 'Software / Tools'),
        ('Hardware', 'Hardware'),
        ('Marketing', 'Marketing'),
        ('Travel', 'Travel'),
        ('Training', 'Training'),
        ('Office', 'Office Supplies'),
        ('Other', 'Other'),
    ])
    attachment  = FileField('Attachment (invoice / receipt)', validators=[
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'webp'], 'PDF or image only!')
    ])
    submit = SubmitField('Submit Proposal')

class ExpenseReviewForm(FlaskForm):
    status       = SelectField('Decision', choices=[('approved', 'Approve'), ('rejected', 'Reject')])
    review_notes = TextAreaField('Notes', validators=[Length(max=1000)])
    submit       = SubmitField('Submit Decision')

class SuggestionForm(FlaskForm):
    title        = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    content      = TextAreaField('Suggestion', validators=[DataRequired(), Length(min=10)])
    category     = SelectField('Category', choices=[
        ('General', 'General'),
        ('Product', 'Product'),
        ('Design', 'Design'),
        ('Process', 'Process'),
        ('Culture', 'Culture'),
        ('Tech', 'Tech / Engineering'),
        ('Other', 'Other'),
    ])
    is_anonymous = BooleanField('Submit anonymously')
    submit       = SubmitField('Submit Suggestion')

class JobListingForm(FlaskForm):
    title        = StringField('Job Title', validators=[DataRequired(), Length(min=3, max=200)])
    department   = StringField('Department', validators=[Length(max=100)])
    description  = TextAreaField('Job Description', validators=[DataRequired(), Length(min=20)])
    requirements = TextAreaField('Requirements', validators=[Length(max=2000)])
    salary_range = StringField('Salary Range', validators=[Length(max=100)])
    location     = StringField('Location', validators=[Length(max=100)])
    job_type     = SelectField('Job Type', choices=[
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
        ('Freelance', 'Freelance'),
    ])
    is_active    = BooleanField('Active (visible to applicants)', default=True)
    submit       = SubmitField('Post Job')

class JobApplicationForm(FlaskForm):
    applicant_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email          = EmailField('Email', validators=[DataRequired(), Email()])
    phone          = StringField('Phone', validators=[Length(max=30)])
    cover_letter   = TextAreaField('Cover Letter', validators=[DataRequired(), Length(min=50)])
    resume         = FileField('Resume / CV', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'png', 'jpg'], 'PDF, DOC or image only!')
    ])
    submit         = SubmitField('Submit Application')

class ApplicationReviewForm(FlaskForm):
    status       = SelectField('Decision', choices=[('approved', 'Approve'), ('rejected', 'Reject')])
    review_notes = TextAreaField('Notes / Feedback', validators=[Length(max=1000)])
    submit       = SubmitField('Submit Decision')
