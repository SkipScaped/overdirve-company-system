// Gallery Component using React Virtual DOM
class GalleryItem extends React.Component {
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
    const { image } = this.props;
    const { isHovered } = this.state;
    
    const itemStyle = {
      transform: isHovered ? 'translateY(-5px)' : 'translateY(0)',
      boxShadow: isHovered ? '0 10px 20px rgba(0,0,0,0.2)' : '0 5px 15px rgba(0,0,0,0.2)',
      borderColor: isHovered ? '#5bae4a' : '#828282',
      transition: 'all 0.3s ease'
    };
    
    const imageStyle = {
      filter: isHovered ? 'brightness(1.1)' : 'brightness(1)',
      transition: 'all 0.3s ease'
    };

    return (
      <div 
        className="gallery-item" 
        style={itemStyle}
        onMouseEnter={this.handleMouseEnter}
        onMouseLeave={this.handleMouseLeave}
      >
        <a href={`/image/${image.id}`} data-toggle="lightbox" data-title={image.title}>
          <img 
            src={image.filepath} 
            alt={image.title} 
            className="img-fluid"
            style={imageStyle}
          />
        </a>
        <div className="gallery-item-caption">
          <div className="gallery-item-category">{image.category}</div>
          <h3 className="gallery-item-title">{image.title}</h3>
          <div className="gallery-item-uploader">
            <i className="fas fa-user"></i> {' '}
            {image.user_id ? (
              <a href={`/user/${image.user_id}`}>{image.uploader}</a>
            ) : (
              image.uploader
            )}
          </div>
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
    );
  }
}

class GalleryGrid extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      images: [],
      loading: true,
      error: null
    };
  }

  componentDidMount() {
    // Use the images passed from the data attribute or fetch from API
    const galleryContainer = document.getElementById('react-gallery');
    if (galleryContainer) {
      try {
        const imagesData = JSON.parse(galleryContainer.getAttribute('data-images'));
        this.setState({ 
          images: imagesData,
          loading: false 
        });
      } catch (error) {
        console.error('Error parsing gallery data:', error);
        this.setState({ 
          error: 'Failed to load images',
          loading: false
        });
      }
    }
  }

  render() {
    const { images, loading, error } = this.state;

    if (loading) {
      return <div className="text-center p-5"><i className="fas fa-spinner fa-spin fa-3x"></i></div>;
    }

    if (error) {
      return <div className="alert alert-danger">{error}</div>;
    }

    if (images.length === 0) {
      return (
        <div className="alert alert-warning">
          <i className="fas fa-exclamation-triangle"></i> No images have been uploaded yet. Be the first to share your Minecraft creations!
        </div>
      );
    }

    return (
      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        {images.map((image) => (
          <div className="col" key={image.id}>
            <GalleryItem image={image} />
          </div>
        ))}
      </div>
    );
  }
}

// Initialize React components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const galleryContainer = document.getElementById('react-gallery');
  if (galleryContainer) {
    ReactDOM.render(<GalleryGrid />, galleryContainer);
  }
});