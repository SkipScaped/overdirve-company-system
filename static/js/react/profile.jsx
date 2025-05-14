// Profile Component using React Virtual DOM
class ProfileCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isHovered: false
    };
  }

  handleMouseEnter = () => {
    this.setState({ isHovered: true });
  }

  handleMouseLeave = () => {
    this.setState({ isHovered: false });
  }

  render() {
    const { user, isCurrentUser, imageCount, joinDate } = this.props;
    const { isHovered } = this.state;
    
    const cardStyle = {
      transform: isHovered ? 'translateY(-5px)' : 'translateY(0)',
      boxShadow: isHovered ? '0 8px 20px rgba(0,0,0,0.2)' : '0 5px 10px rgba(0,0,0,0.2)',
      borderColor: isHovered ? '#5bae4a' : '#828282',
      transition: 'all 0.3s ease'
    };
    
    const imageStyle = {
      transform: isHovered ? 'scale(1.05)' : 'scale(1)',
      borderColor: isHovered ? '#00cfcf' : '#5bae4a',
      transition: 'all 0.3s ease',
      width: '150px',
      height: '150px',
      objectFit: 'cover'
    };

    return (
      <div 
        className="profile-card p-4 bg-white border rounded shadow-sm"
        style={cardStyle}
        onMouseEnter={this.handleMouseEnter}
        onMouseLeave={this.handleMouseLeave}
      >
        <div className="text-center mb-4">
          <img 
            src={user.profile_pic} 
            alt={user.username} 
            className="profile-image img-fluid rounded-circle mb-3"
            style={imageStyle}
          />
          <h2 className="profile-username">{user.username}</h2>
          {user.minecraft_username && (
            <p className="text-muted">Minecraft: {user.minecraft_username}</p>
          )}
        </div>
        
        <div className="profile-stats d-flex justify-content-around mb-4">
          <div className="text-center">
            <h4>{imageCount}</h4>
            <small className="text-muted">Uploads</small>
          </div>
          <div className="text-center">
            <h4>{joinDate}</h4>
            <small className="text-muted">Joined</small>
          </div>
        </div>
        
        {user.bio && (
          <div className="profile-bio mb-4">
            <h5>About Me</h5>
            <p>{user.bio}</p>
          </div>
        )}
        
        {isCurrentUser && (
          <div className="profile-actions d-grid gap-2">
            <a href="/profile/edit" className="btn btn-minecraft">
              <i className="fas fa-user-edit"></i> Edit Profile
            </a>
            <a href="/profile/change_password" className="btn btn-outline-secondary">
              <i className="fas fa-key"></i> Change Password
            </a>
          </div>
        )}
      </div>
    );
  }
}

class UserProfile extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      userImages: [],
      loading: true,
      error: null
    };
  }

  componentDidMount() {
    // Use the data passed from the data attribute
    const profileContainer = document.getElementById('react-profile');
    if (profileContainer) {
      try {
        const userData = JSON.parse(profileContainer.getAttribute('data-user'));
        const userImages = JSON.parse(profileContainer.getAttribute('data-images'));
        const isCurrentUser = profileContainer.getAttribute('data-is-current-user') === 'true';
        
        this.setState({ 
          user: userData,
          userImages: userImages,
          isCurrentUser: isCurrentUser,
          loading: false
        });
      } catch (error) {
        console.error('Error parsing profile data:', error);
        this.setState({ 
          error: 'Failed to load profile data',
          loading: false
        });
      }
    }
  }

  formatDate(dateString) {
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }

  render() {
    const { user, userImages, isCurrentUser, loading, error } = this.state;

    if (loading) {
      return <div className="text-center p-5"><i className="fas fa-spinner fa-spin fa-3x"></i></div>;
    }

    if (error) {
      return <div className="alert alert-danger">{error}</div>;
    }

    if (!user) {
      return <div className="alert alert-warning">User not found</div>;
    }

    const joinDate = this.formatDate(user.created_at);

    return (
      <div className="row">
        <div className="col-lg-4 mb-4">
          <ProfileCard 
            user={user} 
            isCurrentUser={isCurrentUser} 
            imageCount={userImages.length}
            joinDate={joinDate}
          />
        </div>
        
        <div className="col-lg-8">
          <h3><i className="fas fa-camera-retro"></i> {user.username}'s Uploads</h3>
          
          {userImages.length > 0 ? (
            <div className="row row-cols-1 row-cols-md-2 g-4">
              {userImages.map((image) => (
                <div className="col" key={image.id}>
                  <div className="gallery-item">
                    <a href={`/image/${image.id}`} data-toggle="lightbox" data-title={image.title}>
                      <img src={image.filepath} alt={image.title} className="img-fluid" />
                    </a>
                    <div className="gallery-item-caption">
                      <div className="gallery-item-category">{image.category}</div>
                      <h3 className="gallery-item-title">{image.title}</h3>
                      <p className="gallery-item-description">
                        {image.description.length > 100 
                          ? `${image.description.substring(0, 100)}...` 
                          : image.description}
                      </p>
                      <a href={`/image/${image.id}`} className="btn btn-sm btn-minecraft">
                        <i className="fas fa-eye"></i> View Details
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="alert alert-light">
              <i className="fas fa-info-circle"></i> No images have been uploaded yet.
              {isCurrentUser && (
                <a href="/upload" className="alert-link"> Upload your first image!</a>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }
}

// Initialize React components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const profileContainer = document.getElementById('react-profile');
  if (profileContainer) {
    ReactDOM.render(<UserProfile />, profileContainer);
  }
});