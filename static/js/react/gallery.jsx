// Gallery Component
const PLACEHOLDER_SRC = '/static/images/placeholder.svg';

class GalleryItem extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hovered: false };
  }

  render() {
    const { image } = this.props;
    const { hovered } = this.state;
    return (
      <div
        className="gallery-item"
        style={{ transform: hovered ? 'translateY(-5px)' : 'none', transition: 'transform .2s' }}
        onMouseEnter={() => this.setState({ hovered: true })}
        onMouseLeave={() => this.setState({ hovered: false })}
      >
        <a href={`/image/${image.id}`} style={{ textDecoration: 'none', display: 'block' }}>
          <div className="img-wrap position-relative">
            <img
              src={image.filepath}
              alt={image.title}
              onError={(e) => {
                if (e.target.src !== PLACEHOLDER_SRC) e.target.src = PLACEHOLDER_SRC;
              }}
            />
            <span className="gallery-item-category">{image.category}</span>
            <div className="img-overlay">
              <span><i className="fas fa-eye"></i> View</span>
            </div>
          </div>
        </a>
        <div className="gallery-item-caption">
          <div className="gallery-item-title">{image.title}</div>
          <div className="gallery-item-uploader">
            <i className="fas fa-user"></i>{' '}
            {image.user_id
              ? <a href={`/user/${image.user_id}`} style={{ color: 'inherit' }}>{image.uploader}</a>
              : image.uploader}
          </div>
          <p className="gallery-item-description">
            {image.description.length > 80
              ? image.description.substring(0, 80) + '…'
              : image.description}
          </p>
          <a href={`/image/${image.id}`} className="btn btn-sm btn-minecraft">
            <i className="fas fa-eye"></i> View
          </a>
        </div>
      </div>
    );
  }
}

class GalleryGrid extends React.Component {
  constructor(props) {
    super(props);
    this.state = { images: [], loading: true, error: null };
  }

  componentDidMount() {
    const el = document.getElementById('react-gallery');
    if (el) {
      try {
        const data = JSON.parse(el.getAttribute('data-images') || '[]');
        this.setState({ images: data, loading: false });
      } catch (e) {
        this.setState({ error: 'Could not load images.', loading: false });
      }
    }
  }

  render() {
    const { images, loading, error } = this.state;
    if (loading) return (
      <div className="text-center py-5" style={{ color: '#5bae4a' }}>
        <i className="fas fa-spinner fa-spin fa-2x"></i>
        <p style={{ fontFamily: 'VT323, monospace', fontSize: '22px', marginTop: '10px' }}>Loading…</p>
      </div>
    );
    if (error) return <div className="alert alert-danger">{error}</div>;
    if (images.length === 0) return (
      <div style={{
        textAlign: 'center', padding: '48px 24px',
        background: '#fff', borderRadius: '12px',
        boxShadow: '0 4px 16px rgba(0,0,0,.1)'
      }}>
        <i className="fas fa-images" style={{ fontSize: '3rem', color: '#ccc', display: 'block', marginBottom: '12px' }}></i>
        <p style={{ fontFamily: 'VT323, monospace', fontSize: '24px', color: '#7d5736' }}>No Images Yet!</p>
        <p style={{ color: '#888', fontSize: '14px' }}>Be the first to share your Minecraft screenshots.</p>
        <a href="/upload" className="btn btn-minecraft" style={{ marginTop: '8px' }}>
          <i className="fas fa-upload"></i> Upload First Image
        </a>
      </div>
    );
    return (
      <div className="row row-cols-2 row-cols-md-2 row-cols-lg-3 g-3">
        {images.map(image => (
          <div className="col" key={image.id}>
            <GalleryItem image={image} />
          </div>
        ))}
      </div>
    );
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const el = document.getElementById('react-gallery');
  if (el) ReactDOM.render(<GalleryGrid />, el);
});
