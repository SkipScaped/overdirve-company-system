def allowed_file(filename):
    """Check if a file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_categories(images):
    """Extract unique categories from the images list"""
    categories = set()
    for image in images:
        categories.add(image.get('category', 'Other'))
    return sorted(list(categories))

def format_date(date_string):
    """Format a date string for display"""
    from datetime import datetime
    try:
        date_obj = datetime.fromisoformat(date_string)
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return date_string
