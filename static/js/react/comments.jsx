// Comments Component using React Virtual DOM
class Comment extends React.Component {
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

  formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }

  render() {
    const { comment } = this.props;
    const { isHovered } = this.state;
    
    const commentStyle = {
      borderLeftColor: isHovered ? '#5bae4a' : null,
      backgroundColor: isHovered ? '#f0f0f0' : '#f5f5f5',
      transition: 'all 0.3s ease'
    };

    return (
      <div 
        className="comment"
        style={commentStyle}
        onMouseEnter={this.handleMouseEnter}
        onMouseLeave={this.handleMouseLeave}
      >
        <div className="comment-meta">
          <span className="comment-username">
            {comment.user_id ? (
              <a href={`/user/${comment.user_id}`}>{comment.username}</a>
            ) : (
              comment.username
            )}
          </span>
          <span className="comment-date">{this.formatDate(comment.created_at)}</span>
        </div>
        <div className="comment-text">
          {comment.text}
        </div>
      </div>
    );
  }
}

class CommentList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      comments: [],
      newComment: '',
      username: '',
      loading: true,
      error: null,
      isLoggedIn: false
    };
  }

  componentDidMount() {
    // Use the comments passed from the data attribute
    const commentsContainer = document.getElementById('react-comments');
    if (commentsContainer) {
      try {
        const commentsData = JSON.parse(commentsContainer.getAttribute('data-comments'));
        const isLoggedIn = commentsContainer.getAttribute('data-logged-in') === 'true';
        const imageId = commentsContainer.getAttribute('data-image-id');
        const username = commentsContainer.getAttribute('data-username') || '';
        
        this.setState({ 
          comments: commentsData,
          loading: false,
          isLoggedIn,
          imageId,
          username
        });
      } catch (error) {
        console.error('Error parsing comments data:', error);
        this.setState({ 
          error: 'Failed to load comments',
          loading: false
        });
      }
    }
  }

  handleInputChange = (e) => {
    this.setState({ [e.target.name]: e.target.value });
  }

  handleSubmit = (e) => {
    e.preventDefault();
    // In a real application, this would submit to the server via AJAX
    // For now, redirect to the form submission
    document.querySelector('form.comment-form').submit();
  }

  render() {
    const { comments, loading, error, isLoggedIn, username, newComment } = this.state;

    if (loading) {
      return <div className="text-center p-3"><i className="fas fa-spinner fa-spin"></i> Loading comments...</div>;
    }

    if (error) {
      return <div className="alert alert-danger">{error}</div>;
    }

    return (
      <div className="comments-section">
        <h3><i className="fas fa-comments"></i> Comments ({comments.length})</h3>
        
        <div className="comment-form mb-4">
          {isLoggedIn ? (
            <form onSubmit={this.handleSubmit} className="comment-form">
              <div className="mb-3">
                <label htmlFor="username" className="form-label">Your Name</label>
                <input 
                  type="text" 
                  className="form-control" 
                  id="username"
                  name="username"
                  value={username}
                  onChange={this.handleInputChange}
                  placeholder="Your Minecraft username"
                  required
                />
              </div>
              
              <div className="mb-3">
                <label htmlFor="text" className="form-label">Comment</label>
                <textarea 
                  className="form-control" 
                  id="text"
                  name="newComment"
                  value={newComment}
                  onChange={this.handleInputChange}
                  rows="3"
                  placeholder="Share your thoughts about this image..."
                  required
                ></textarea>
              </div>
              
              <button type="submit" className="btn btn-minecraft">
                <i className="fas fa-paper-plane"></i> Post Comment
              </button>
            </form>
          ) : (
            <div className="alert alert-info">
              <i className="fas fa-info-circle"></i> 
              <a href="/login">Log in</a> or 
              <a href="/register"> sign up</a> 
              to leave a comment.
            </div>
          )}
        </div>
        
        {comments.length > 0 ? (
          comments.map((comment) => (
            <Comment key={comment.id} comment={comment} />
          ))
        ) : (
          <div className="alert alert-light">
            <i className="fas fa-info-circle"></i> No comments yet. Be the first to comment!
          </div>
        )}
      </div>
    );
  }
}

// Initialize React components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const commentsContainer = document.getElementById('react-comments');
  if (commentsContainer) {
    ReactDOM.render(<CommentList />, commentsContainer);
  }
});