import json
import os
from datetime import datetime

# Data file paths
DATA_DIR = 'data'
IMAGES_DATA_FILE = os.path.join(DATA_DIR, 'images.json')
COMMENTS_DATA_FILE = os.path.join(DATA_DIR, 'comments.json')

# Create data directory if not exists
os.makedirs(DATA_DIR, exist_ok=True)

# Image functions
def load_images():
    """Load all images from the data file"""
    if not os.path.exists(IMAGES_DATA_FILE):
        return []
    
    try:
        with open(IMAGES_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_images(images):
    """Save all images to the data file"""
    with open(IMAGES_DATA_FILE, 'w') as f:
        json.dump(images, f, indent=4)

def save_image(image_data):
    """Add a new image to the data file"""
    images = load_images()
    images.append(image_data)
    save_images(images)
    return image_data

def get_image_by_id(image_id):
    """Get an image by its ID"""
    images = load_images()
    for image in images:
        if image['id'] == image_id:
            return image
    return None

def update_image(image_id, updated_data):
    """Update an existing image"""
    images = load_images()
    for i, image in enumerate(images):
        if image['id'] == image_id:
            images[i].update(updated_data)
            save_images(images)
            return images[i]
    return None

def delete_image(image_id):
    """Delete an image by its ID"""
    images = load_images()
    images = [img for img in images if img['id'] != image_id]
    save_images(images)

# Comment functions
def load_comments():
    """Load all comments from the data file"""
    if not os.path.exists(COMMENTS_DATA_FILE):
        return []
    
    try:
        with open(COMMENTS_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_comments(comments):
    """Save all comments to the data file"""
    with open(COMMENTS_DATA_FILE, 'w') as f:
        json.dump(comments, f, indent=4)

def save_comment(comment_data):
    """Add a new comment to the data file"""
    comments = load_comments()
    comments.append(comment_data)
    save_comments(comments)
    return comment_data

def get_comments_for_image(image_id):
    """Get all comments for a specific image"""
    comments = load_comments()
    return [c for c in comments if c['image_id'] == image_id]

def delete_comment(comment_id):
    """Delete a comment by its ID"""
    comments = load_comments()
    comments = [c for c in comments if c['id'] != comment_id]
    save_comments(comments)

# Sample data initialization
def initialize_sample_data():
    """Initialize with sample Minecraft images if the database is empty"""
    images = load_images()
    if images:
        return  # Don't initialize if data already exists
    
    sample_images = [
        {
            'id': '1',
            'title': 'Mountain Base',
            'description': 'An epic mountain base with integrated redstone systems',
            'category': 'Builds',
            'filename': 'minecraft_build_1.jpg',
            'filepath': '/static/images/samples/minecraft_build_1.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'MCBuilder'
        },
        {
            'id': '2',
            'title': 'Medieval Village',
            'description': 'A sprawling medieval village with custom architecture',
            'category': 'Builds',
            'filename': 'minecraft_build_2.jpg', 
            'filepath': '/static/images/samples/minecraft_build_2.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'MedievalCrafter'
        },
        {
            'id': '3',
            'title': 'Sunset Over Mesa',
            'description': 'Beautiful mesa biome at sunset',
            'category': 'Landscapes',
            'filename': 'minecraft_landscape_1.jpg',
            'filepath': '/static/images/samples/minecraft_landscape_1.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'BiomeExplorer'
        },
        {
            'id': '4',
            'title': 'Jungle Temple',
            'description': 'Ancient jungle temple with custom decorations',
            'category': 'Builds',
            'filename': 'minecraft_build_3.jpg',
            'filepath': '/static/images/samples/minecraft_build_3.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'TempleBuilder'
        },
        {
            'id': '5',
            'title': 'SMP Spawn Area',
            'description': 'Our server\'s main spawn with shops and meeting hall',
            'category': 'Servers',
            'filename': 'minecraft_server_1.jpg',
            'filepath': '/static/images/samples/minecraft_server_1.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'ServerAdmin'
        },
        {
            'id': '6',
            'title': 'Redstone Contraption',
            'description': 'Automatic sorting system using hoppers and redstone',
            'category': 'Builds',
            'filename': 'minecraft_build_4.jpg',
            'filepath': '/static/images/samples/minecraft_build_4.jpg',
            'uploaded_at': datetime.now().isoformat(),
            'uploader': 'RedstoneGenius'
        }
    ]
    
    save_images(sample_images)
    
    sample_comments = [
        {
            'id': '1',
            'image_id': '1',
            'username': 'MineExpert',
            'text': 'Amazing build! How long did this take?',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': '2',
            'image_id': '1',
            'username': 'MCBuilder',
            'text': 'About 3 weeks of work. The redstone was the hardest part!',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': '3',
            'image_id': '3',
            'username': 'SceneryLover',
            'text': 'What shaders are you using? The lighting is beautiful!',
            'created_at': datetime.now().isoformat()
        }
    ]
    
    save_comments(sample_comments)
