// Minecraft SMP Gallery - Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Image upload preview
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    }
    
    // React comment form submission handler
    document.addEventListener('react-comment-submit', function(e) {
        const hiddenUsernameField = document.getElementById('hidden_username');
        const hiddenTextField = document.getElementById('hidden_text');
        
        if (hiddenUsernameField && hiddenTextField && e.detail) {
            hiddenUsernameField.value = e.detail.username;
            hiddenTextField.value = e.detail.text;
            
            // Submit the form
            document.querySelector('form.comment-form').submit();
        }
    });
    
    // Profile image hover effect
    const profileImage = document.querySelector('.profile-image');
    if (profileImage) {
        profileImage.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.borderColor = '#00cfcf'; // Diamond color
        });
        
        profileImage.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.borderColor = '';
        });
    }
    
    // Make gallery items pixel perfect on mobile
    function adjustGalleryItems() {
        const galleryItems = document.querySelectorAll('.gallery-item');
        if (window.innerWidth < 576) {
            galleryItems.forEach(item => {
                item.style.imageRendering = 'pixelated';
            });
        } else {
            galleryItems.forEach(item => {
                item.style.imageRendering = '';
            });
        }
    }
    
    // Initial call and listen for resize
    adjustGalleryItems();
    window.addEventListener('resize', adjustGalleryItems);
    
    // Add pixel border animation to buttons
    const minecraftButtons = document.querySelectorAll('.btn-minecraft');
    minecraftButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2), inset -2px -2px 0 rgba(0,0,0,0.3)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = 'inset -2px -2px 0 rgba(0,0,0,0.3)';
        });
        
        button.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2), inset 2px 2px 0 rgba(0,0,0,0.3)';
        });
        
        button.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2), inset -2px -2px 0 rgba(0,0,0,0.3)';
        });
    });
});