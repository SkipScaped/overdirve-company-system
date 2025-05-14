import os
import uuid
from datetime import datetime
from app import db

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.Column(db.String(50), nullable=False)
    
    # Relationship with comments
    comments = db.relationship('Comment', backref='image', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'filename': self.filename,
            'filepath': self.filepath,
            'uploaded_at': self.uploaded_at.isoformat(),
            'uploader': self.uploader
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True)
    image_id = db.Column(db.String(36), db.ForeignKey('images.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'username': self.username,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }

# Utility functions to work with the database
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
            uploaded_at=uploaded_at,
            uploader=image_data['uploader']
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
            created_at=created_at
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
