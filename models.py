import os
import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


# ─── NEW: Company Management Models ──────────────────────────────────────────

class CompanyUpdate(db.Model):
    __tablename__ = 'company_updates'
    id         = db.Column(db.String(36), primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    category   = db.Column(db.String(50), default='General')
    is_pinned  = db.Column(db.Boolean, default=False)
    author_id  = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author     = db.relationship('User', foreign_keys=[author_id], backref='company_updates')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class ExpenseProposal(db.Model):
    __tablename__ = 'expense_proposals'
    id           = db.Column(db.String(36), primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text, nullable=False)
    amount       = db.Column(db.Float, nullable=False)
    currency     = db.Column(db.String(10), default='USD')
    category     = db.Column(db.String(50), default='General')
    status       = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    submitter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewer_id  = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    review_notes = db.Column(db.Text, default='')
    file_path    = db.Column(db.String(255), default='')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at  = db.Column(db.DateTime, nullable=True)
    submitter    = db.relationship('User', foreign_keys=[submitter_id], backref='expense_proposals')
    reviewer     = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewed_expenses')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class Suggestion(db.Model):
    __tablename__ = 'suggestions'
    id           = db.Column(db.String(36), primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    content      = db.Column(db.Text, nullable=False)
    category     = db.Column(db.String(50), default='General')
    is_anonymous = db.Column(db.Boolean, default=False)
    status       = db.Column(db.String(20), default='open')  # open/reviewed/implemented/closed
    submitter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    submitter    = db.relationship('User', foreign_keys=[submitter_id], backref='suggestions')
    votes        = db.relationship('SuggestionVote', backref='suggestion', lazy=True, cascade='all, delete-orphan')

    def vote_count(self):
        return len(self.votes)

    def user_voted(self, user_id):
        return any(v.user_id == user_id for v in self.votes)

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class SuggestionVote(db.Model):
    __tablename__ = 'suggestion_votes'
    id            = db.Column(db.String(36), primary_key=True)
    suggestion_id = db.Column(db.String(36), db.ForeignKey('suggestions.id'), nullable=False)
    user_id       = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class JobListing(db.Model):
    __tablename__ = 'job_listings'
    id           = db.Column(db.String(36), primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    department   = db.Column(db.String(100), default='')
    description  = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, default='')
    salary_range = db.Column(db.String(100), default='Competitive')
    location     = db.Column(db.String(100), default='Remote')
    job_type     = db.Column(db.String(50), default='Full-time')
    is_active    = db.Column(db.Boolean, default=True)
    created_by   = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    creator      = db.relationship('User', foreign_keys=[created_by], backref='job_listings')
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id              = db.Column(db.String(36), primary_key=True)
    job_id          = db.Column(db.String(36), db.ForeignKey('job_listings.id'), nullable=False)
    applicant_name  = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(120), nullable=False)
    phone           = db.Column(db.String(30), default='')
    cover_letter    = db.Column(db.Text, nullable=False)
    resume_path     = db.Column(db.String(255), default='')
    status          = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    reviewer_id     = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    review_notes    = db.Column(db.Text, default='')
    user_id         = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at     = db.Column(db.DateTime, nullable=True)
    reviewer        = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewed_applications')
    applicant_user  = db.relationship('User', foreign_keys=[user_id], backref='job_applications')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)

class ServerConfig(db.Model):
    __tablename__ = 'server_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)

    @staticmethod
    def get(key, default=''):
        row = ServerConfig.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = ServerConfig.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            row = ServerConfig(key=key, value=value)
            db.session.add(row)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_pic = db.Column(db.String(255), default='static/images/default_avatar.png')
    pic_data = db.Column(db.LargeBinary)
    pic_mime = db.Column(db.String(50), default='image/jpeg')
    bio = db.Column(db.Text, default='')
    minecraft_username = db.Column(db.String(50), default='')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    images = db.relationship('Image', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        if 'password' in kwargs:
            self.set_password(kwargs.pop('password'))
        super(User, self).__init__(**kwargs)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def profile_pic_url(self):
        if self.pic_data:
            return f'/profile-pic/{self.id}'
        pic = self.profile_pic or 'static/images/default_avatar.png'
        if not pic.startswith('/'):
            pic = '/' + pic
        return pic

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'profile_pic': self.profile_pic_url,
            'bio': self.bio,
            'minecraft_username': self.minecraft_username,
            'created_at': self.created_at.isoformat()
        }

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary)
    mime_type = db.Column(db.String(50), default='image/jpeg')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Relationship with comments
    comments = db.relationship('Comment', backref='image', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super(Image, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'filename': self.filename,
            'filepath': f'/img/{self.id}',
            'uploaded_at': self.uploaded_at.isoformat(),
            'uploader': self.uploader,
            'user_id': self.user_id
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True)
    image_id = db.Column(db.String(36), db.ForeignKey('images.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super(Comment, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'username': self.username,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }

# Utility functions to work with the database
class DirectMessage(db.Model):
    __tablename__ = 'direct_messages'

    id = db.Column(db.String(36), primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class GroupMessage(db.Model):
    __tablename__ = 'group_messages'

    id = db.Column(db.String(36), primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='group_messages')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class ShopCategory(db.Model):
    __tablename__ = 'shop_categories'
    id          = db.Column(db.String(36), primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    image_path  = db.Column(db.String(255), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    products    = db.relationship('ShopProduct', backref='category', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


class ShopProduct(db.Model):
    __tablename__ = 'shop_products'
    id          = db.Column(db.String(36), primary_key=True)
    category_id = db.Column(db.String(36), db.ForeignKey('shop_categories.id'), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    price       = db.Column(db.String(50), nullable=False, default='Free')
    image_path  = db.Column(db.String(255), default='')
    in_stock    = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)


def load_images():
    """Load all images from the database"""
    try:
        return [image.to_dict() for image in Image.query.order_by(Image.uploaded_at.desc()).all()]
    except Exception as e:
        print(f"Error loading images: {e}")
        return []

def save_image(image_data):
    """Add a new image to the database"""
    try:
        if 'id' not in image_data:
            image_data['id'] = str(uuid.uuid4())
        
        # Convert date if it's a string
        if isinstance(image_data.get('uploaded_at'), str):
            uploaded_at = datetime.fromisoformat(image_data['uploaded_at'])
        else:
            uploaded_at = image_data.get('uploaded_at', datetime.utcnow())
        
        image = Image(
            id=image_data['id'],
            title=image_data['title'],
            description=image_data['description'],
            category=image_data['category'],
            filename=image_data['filename'],
            filepath=image_data['filepath'],
            file_data=image_data.get('file_data'),
            mime_type=image_data.get('mime_type', 'image/jpeg'),
            uploaded_at=uploaded_at,
            uploader=image_data['uploader'],
            user_id=image_data.get('user_id')
        )
        
        db.session.add(image)
        db.session.commit()
        return image.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving image: {e}")
        return None

def get_image_by_id(image_id):
    """Get an image by its ID"""
    try:
        image = Image.query.get(image_id)
        return image.to_dict() if image else None
    except Exception as e:
        print(f"Error getting image by ID: {e}")
        return None

def update_image(image_id, updated_data):
    """Update an existing image"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return None
        
        for key, value in updated_data.items():
            if key in ['title', 'description', 'category', 'filename', 'filepath', 'uploader']:
                setattr(image, key, value)
        
        db.session.commit()
        return image.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating image: {e}")
        return None

def delete_image(image_id):
    """Delete an image by its ID"""
    try:
        image = Image.query.get(image_id)
        if image:
            db.session.delete(image)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting image: {e}")

def load_comments():
    """Load all comments from the database"""
    try:
        return [comment.to_dict() for comment in Comment.query.order_by(Comment.created_at.desc()).all()]
    except Exception as e:
        print(f"Error loading comments: {e}")
        return []

def save_comment(comment_data):
    """Add a new comment to the database"""
    try:
        if 'id' not in comment_data:
            comment_data['id'] = str(uuid.uuid4())
        
        # Convert date if it's a string
        if isinstance(comment_data.get('created_at'), str):
            created_at = datetime.fromisoformat(comment_data['created_at'])
        else:
            created_at = comment_data.get('created_at', datetime.utcnow())
        
        comment = Comment(
            id=comment_data['id'],
            image_id=comment_data['image_id'],
            username=comment_data['username'],
            text=comment_data['text'],
            created_at=created_at,
            user_id=comment_data.get('user_id')
        )
        
        db.session.add(comment)
        db.session.commit()
        return comment.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving comment: {e}")
        return None

def get_comments_for_image(image_id):
    """Get all comments for a specific image"""
    try:
        comments = Comment.query.filter_by(image_id=image_id).order_by(Comment.created_at.desc()).all()
        return [comment.to_dict() for comment in comments]
    except Exception as e:
        print(f"Error getting comments for image: {e}")
        return []

def delete_comment(comment_id):
    """Delete a comment by its ID"""
    try:
        comment = Comment.query.get(comment_id)
        if comment:
            db.session.delete(comment)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting comment: {e}")

# Sample data initialization
def initialize_sample_data():
    """Initialize with sample Minecraft images if the database is empty"""
    try:
        # Check if any images exist already
        if Image.query.first():
            return  # Don't initialize if data already exists
        
        sample_images = [
            {
                'id': str(uuid.uuid4()),
                'title': 'Mountain Base',
                'description': 'An epic mountain base with integrated redstone systems',
                'category': 'Builds',
                'filename': 'minecraft_build_1.jpg',
                'filepath': '/static/images/samples/minecraft_build_1.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'MCBuilder'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Medieval Village',
                'description': 'A sprawling medieval village with custom architecture',
                'category': 'Builds',
                'filename': 'minecraft_build_2.jpg', 
                'filepath': '/static/images/samples/minecraft_build_2.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'MedievalCrafter'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Sunset Over Mesa',
                'description': 'Beautiful mesa biome at sunset',
                'category': 'Landscapes',
                'filename': 'minecraft_landscape_1.jpg',
                'filepath': '/static/images/samples/minecraft_landscape_1.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'BiomeExplorer'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Jungle Temple',
                'description': 'Ancient jungle temple with custom decorations',
                'category': 'Builds',
                'filename': 'minecraft_build_3.jpg',
                'filepath': '/static/images/samples/minecraft_build_3.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'TempleBuilder'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'SMP Spawn Area',
                'description': 'Our server\'s main spawn with shops and meeting hall',
                'category': 'Servers',
                'filename': 'minecraft_server_1.jpg',
                'filepath': '/static/images/samples/minecraft_server_1.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'ServerAdmin'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Redstone Contraption',
                'description': 'Automatic sorting system using hoppers and redstone',
                'category': 'Redstone',
                'filename': 'minecraft_build_4.jpg',
                'filepath': '/static/images/samples/minecraft_build_4.jpg',
                'uploaded_at': datetime.utcnow(),
                'uploader': 'RedstoneGenius'
            }
        ]
        
        # Add sample images
        added_images = []
        for image_data in sample_images:
            image = Image(
                id=image_data['id'],
                title=image_data['title'],
                description=image_data['description'],
                category=image_data['category'],
                filename=image_data['filename'],
                filepath=image_data['filepath'],
                uploaded_at=image_data['uploaded_at'],
                uploader=image_data['uploader']
            )
            db.session.add(image)
            added_images.append(image)
        
        db.session.commit()
        
        # Add sample comments if we have at least 2 images
        if len(added_images) >= 2:
            sample_comments = [
                {
                    'id': str(uuid.uuid4()),
                    'image_id': added_images[0].id,
                    'username': 'MineExpert',
                    'text': 'Amazing build! How long did this take?',
                    'created_at': datetime.utcnow()
                },
                {
                    'id': str(uuid.uuid4()),
                    'image_id': added_images[0].id,
                    'username': 'MCBuilder',
                    'text': 'About 3 weeks of work. The redstone was the hardest part!',
                    'created_at': datetime.utcnow()
                },
                {
                    'id': str(uuid.uuid4()),
                    'image_id': added_images[1].id,
                    'username': 'SceneryLover',
                    'text': 'What shaders are you using? The lighting is beautiful!',
                    'created_at': datetime.utcnow()
                }
            ]
            
            for comment_data in sample_comments:
                comment = Comment(
                    id=comment_data['id'],
                    image_id=comment_data['image_id'],
                    username=comment_data['username'],
                    text=comment_data['text'],
                    created_at=comment_data['created_at']
                )
                db.session.add(comment)
            
            db.session.commit()
            
            print("Successfully initialized sample data")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing sample data: {e}")
