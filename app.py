import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB upload

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Import other modules after db is initialized
from models import load_images, save_image, get_image_by_id, load_comments, save_comment, get_comments_for_image, initialize_sample_data
from forms import UploadForm, CommentForm
from utils import allowed_file, get_categories

# Initialize database tables
with app.app_context():
    db.create_all()
    initialize_sample_data()

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    from forms import RegistrationForm
    form = RegistrationForm()
    
    if form.validate_on_submit():
        from models import User
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            minecraft_username=form.minecraft_username.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    images = load_images()
    categories = get_categories(images)
    return render_template('auth/register.html', form=form, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    from forms import LoginForm
    form = LoginForm()
    
    if form.validate_on_submit():
        from models import User
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('You have been logged in!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    
    images = load_images()
    categories = get_categories(images)
    return render_template('auth/login.html', form=form, categories=categories)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    images = load_images()
    categories = get_categories(images)
    
    # Get user's uploaded images
    user_images = [img for img in images if img.get('user_id') == current_user.id]
    
    return render_template('auth/profile.html', user=current_user, 
                           user_images=user_images, categories=categories)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from forms import ProfileForm
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
    
    if form.validate_on_submit():
        if form.profile_pic.data:
            # Save profile picture
            filename = secure_filename(form.profile_pic.data.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"profile_{current_user.id}.{extension}"
            
            # Save the file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            form.profile_pic.data.save(filepath)
            
            # Update user profile pic path
            current_user.profile_pic = '/'.join(['static', 'uploads', unique_filename])
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.minecraft_username = form.minecraft_username.data
        current_user.bio = form.bio.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.minecraft_username.data = current_user.minecraft_username
        form.bio.data = current_user.bio
    
    images = load_images()
    categories = get_categories(images)
    return render_template('auth/edit_profile.html', form=form, categories=categories)

@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    from forms import ChangePasswordForm
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    images = load_images()
    categories = get_categories(images)
    return render_template('auth/change_password.html', form=form, categories=categories)

# Routes
@app.route('/')
def index():
    images = load_images()
    categories = get_categories(images)
    return render_template('index.html', images=images, categories=categories)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # Check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['image']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and file.filename and allowed_file(file.filename):
            # Generate a unique filename
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{extension}"
            
            # Save the file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Save image metadata
            image_data = {
                'id': str(uuid.uuid4()),
                'title': form.title.data,
                'description': form.description.data,
                'category': form.category.data,
                'filename': unique_filename,
                'filepath': '/'.join(['static', 'uploads', unique_filename]),  # Web path
                'uploaded_at': datetime.now().isoformat(),
                'uploader': form.uploader.data
            }
            
            save_image(image_data)
            
            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Allowed file types are {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
            
    images = load_images()
    categories = get_categories(images)
    return render_template('upload.html', form=form, categories=categories)

@app.route('/image/<image_id>', methods=['GET', 'POST'])
def image_detail(image_id):
    image = get_image_by_id(image_id)
    if not image:
        abort(404)
        
    image_comments = get_comments_for_image(image_id)
    
    form = CommentForm()
    if form.validate_on_submit():
        comment_data = {
            'id': str(uuid.uuid4()),
            'image_id': image_id,
            'username': form.username.data,
            'text': form.text.data,
            'created_at': datetime.now().isoformat()
        }
        save_comment(comment_data)
        flash('Comment added!', 'success')
        return redirect(url_for('image_detail', image_id=image_id))
    
    images = load_images()
    categories = get_categories(images)
    return render_template('image.html', image=image, comments=image_comments, form=form, categories=categories)

@app.route('/category/<category>')
def category(category):
    images = load_images()
    categories = get_categories(images)
    
    category_images = [img for img in images if img['category'].lower() == category.lower()]
    
    return render_template('category.html', category=category, images=category_images, categories=categories)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    images = load_images()
    categories = get_categories(images)
    
    # Simple search in title, description and category
    results = [img for img in images if 
               query.lower() in img['title'].lower() or 
               query.lower() in img['description'].lower() or
               query.lower() in img['category'].lower()]
    
    return render_template('search.html', query=query, images=results, categories=categories)

@app.errorhandler(404)
def page_not_found(e):
    images = load_images()
    categories = get_categories(images)
    return render_template('404.html', categories=categories), 404

@app.errorhandler(413)
def too_large(e):
    flash('The file is too large. Maximum size is 16MB.', 'danger')
    return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
