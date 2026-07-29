import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
csrf = CSRFProtect(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from models import (
    User, DirectMessage, GroupMessage,
    CompanyUpdate, ExpenseProposal, Suggestion, SuggestionVote,
    JobListing, JobApplication, ServerConfig, Notification,
    Role, UserRole,
    EnergyDrinkBrand, EnergyDrinkProduct, StockMovement, EmailVerification
)

with app.app_context():
    db.create_all()
    # Safely add image_path columns if they don't exist yet
    from sqlalchemy import text
    with db.engine.connect() as _conn:
        for _tbl, _col in [('direct_messages', 'image_path'), ('group_messages', 'image_path')]:
            try:
                _conn.execute(text(f"ALTER TABLE {_tbl} ADD COLUMN {_col} VARCHAR(300)"))
                _conn.commit()
            except Exception:
                _conn.rollback()
    if not ServerConfig.query.filter_by(key='company_name').first():
        ServerConfig.set('company_name', 'Overdrive')
    # Seed default energy drink brand
    if not EnergyDrinkBrand.query.first():
        db.session.add(EnergyDrinkBrand())
        db.session.commit()

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file, prefix='file'):
    if not file or not file.filename:
        return ''
    ext = secure_filename(file.filename).rsplit('.', 1)[-1].lower()
    fname = f"{prefix}_{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, fname))
    return f"/static/uploads/{fname}"

def create_notification(user_id, ntype, title, body='', link=''):
    """Queue a notification for user_id. Caller must db.session.commit()."""
    try:
        n = Notification(user_id=str(user_id), ntype=ntype, title=title[:200],
                         body=body[:500], link=link[:300])
        db.session.add(n)
    except Exception as e:
        logger.warning(f'create_notification error: {e}')

@app.context_processor
def inject_globals():
    unread = 0
    notif_unread = 0
    if current_user.is_authenticated:
        try:
            unread = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
            notif_unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        except Exception:
            pass
    return dict(unread_count=unread, notif_unread=notif_unread, now=datetime.utcnow())

# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    from forms import RegistrationForm
    form = RegistrationForm()
    if form.validate_on_submit():
        is_first = User.query.count() == 0
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            is_admin=is_first
        )
        db.session.add(user)
        db.session.commit()
        if is_first:
            flash('Account created! You have been granted Admin access as the first user.', 'success')
        else:
            flash('Account created! You can now sign in.', 'success')
        return redirect(url_for('login'))
    open_jobs = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).limit(4).all()
    return render_template('auth/register.html', form=form, open_jobs=open_jobs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    from forms import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    open_jobs = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).limit(4).all()
    return render_template('auth/login.html', form=form, open_jobs=open_jobs)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@app.route('/user/<user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('auth/profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from forms import ProfileForm
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
    if form.validate_on_submit():
        if form.profile_pic.data and form.profile_pic.data.filename:
            form.profile_pic.data.seek(0)
            pic_bytes = form.profile_pic.data.read()
            pic_mime = form.profile_pic.data.content_type or 'image/jpeg'
            current_user.pic_data = pic_bytes
            current_user.pic_mime = pic_mime
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template('auth/edit_profile.html', form=form)

@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    from forms import ChangePasswordForm
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated!', 'success')
            return redirect(url_for('profile'))
        flash('Current password is incorrect.', 'danger')
    return render_template('auth/change_password.html', form=form)

@app.route('/profile-pic/<user_id>')
def serve_profile_pic(user_id):
    user = User.query.get(user_id)
    if user and user.pic_data:
        return Response(user.pic_data, mimetype=user.pic_mime or 'image/jpeg',
                        headers={'Cache-Control': 'public, max-age=86400'})
    return redirect(url_for('static', filename='images/default_avatar.png'))

# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    updates = CompanyUpdate.query.order_by(
        CompanyUpdate.is_pinned.desc(), CompanyUpdate.created_at.desc()
    ).limit(10).all()
    recent_expenses = ExpenseProposal.query.filter_by(submitter_id=current_user.id)\
        .order_by(ExpenseProposal.created_at.desc()).limit(5).all()
    recent_suggestions = Suggestion.query.order_by(Suggestion.created_at.desc()).limit(5).all()
    active_jobs = JobListing.query.filter_by(is_active=True).count()
    pending_expenses = ExpenseProposal.query.filter_by(status='pending').count() if current_user.is_admin else \
        ExpenseProposal.query.filter_by(submitter_id=current_user.id, status='pending').count()
    total_members = User.query.count()
    open_suggestions = Suggestion.query.filter_by(status='open').count()
    return render_template('dashboard.html',
        updates=updates,
        recent_expenses=recent_expenses,
        recent_suggestions=recent_suggestions,
        active_jobs=active_jobs,
        pending_expenses=pending_expenses,
        total_members=total_members,
        open_suggestions=open_suggestions,
    )

# ─── Company Updates ─────────────────────────────────────────────────────────

@app.route('/updates')
@login_required
def updates():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    q = CompanyUpdate.query
    if category:
        q = q.filter_by(category=category)
    updates = q.order_by(CompanyUpdate.is_pinned.desc(), CompanyUpdate.created_at.desc())\
               .paginate(page=page, per_page=12, error_out=False)
    categories = db.session.query(CompanyUpdate.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('updates/list.html', updates=updates, categories=categories, current_category=category)

@app.route('/updates/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_update():
    from forms import CompanyUpdateForm
    form = CompanyUpdateForm()
    if form.validate_on_submit():
        update = CompanyUpdate(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            is_pinned=form.is_pinned.data,
            author_id=current_user.id,
        )
        db.session.add(update)
        db.session.commit()
        for u in User.query.filter(User.id != current_user.id).all():
            create_notification(u.id, 'update', f'New update: {update.title}',
                                body=update.content[:120], link=f'/updates/{update.id}')
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Update posted!', 'success')
        return redirect(url_for('updates'))
    return render_template('updates/new.html', form=form)

@app.route('/updates/<update_id>')
@login_required
def view_update(update_id):
    update = CompanyUpdate.query.get_or_404(update_id)
    return render_template('updates/detail.html', update=update)

@app.route('/updates/<update_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_update(update_id):
    update = CompanyUpdate.query.get_or_404(update_id)
    from forms import CompanyUpdateForm
    form = CompanyUpdateForm(obj=update)
    if form.validate_on_submit():
        update.title = form.title.data
        update.content = form.content.data
        update.category = form.category.data
        update.is_pinned = form.is_pinned.data
        update.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Update edited!', 'success')
        return redirect(url_for('view_update', update_id=update.id))
    return render_template('updates/new.html', form=form, editing=True, update=update)

@app.route('/updates/<update_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_update(update_id):
    update = CompanyUpdate.query.get_or_404(update_id)
    db.session.delete(update)
    db.session.commit()
    flash('Update deleted.', 'success')
    return redirect(url_for('updates'))

# ─── Expense Proposals ───────────────────────────────────────────────────────

@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    if current_user.is_admin:
        q = ExpenseProposal.query
        if status_filter:
            q = q.filter_by(status=status_filter)
    else:
        q = ExpenseProposal.query.filter_by(submitter_id=current_user.id)
        if status_filter:
            q = q.filter_by(status=status_filter)
    proposals = q.order_by(ExpenseProposal.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('expenses/list.html', proposals=proposals, status_filter=status_filter)

@app.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    from forms import ExpenseProposalForm
    form = ExpenseProposalForm()
    if form.validate_on_submit():
        file_path = ''
        if form.attachment.data and form.attachment.data.filename:
            file_path = save_upload(form.attachment.data, 'expense')
        proposal = ExpenseProposal(
            title=form.title.data,
            description=form.description.data,
            amount=form.amount.data,
            currency=form.currency.data,
            category=form.category.data,
            submitter_id=current_user.id,
            file_path=file_path,
        )
        db.session.add(proposal)
        db.session.commit()
        flash('Expense proposal submitted!', 'success')
        return redirect(url_for('expenses'))
    return render_template('expenses/new.html', form=form)

@app.route('/expenses/<expense_id>')
@login_required
def view_expense(expense_id):
    proposal = ExpenseProposal.query.get_or_404(expense_id)
    if not current_user.is_admin and proposal.submitter_id != current_user.id:
        abort(403)
    from forms import ExpenseReviewForm
    review_form = ExpenseReviewForm() if current_user.is_admin else None
    return render_template('expenses/detail.html', proposal=proposal, review_form=review_form)

@app.route('/expenses/<expense_id>/review', methods=['POST'])
@login_required
@admin_required
def review_expense(expense_id):
    proposal = ExpenseProposal.query.get_or_404(expense_id)
    from forms import ExpenseReviewForm
    form = ExpenseReviewForm()
    if form.validate_on_submit():
        proposal.status = form.status.data
        proposal.review_notes = form.review_notes.data
        proposal.reviewer_id = current_user.id
        proposal.reviewed_at = datetime.utcnow()
        status_label = 'approved ✓' if proposal.status == 'approved' else 'rejected'
        create_notification(proposal.submitter_id, 'expense',
                            f'Expense {status_label}: {proposal.title}',
                            body=proposal.review_notes[:100] if proposal.review_notes else '',
                            link=f'/expenses/{expense_id}')
        db.session.commit()
        flash(f'Expense proposal {form.status.data}.', 'success')
    return redirect(url_for('view_expense', expense_id=expense_id))

@app.route('/expenses/<expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    proposal = ExpenseProposal.query.get_or_404(expense_id)
    if not current_user.is_admin and proposal.submitter_id != current_user.id:
        abort(403)
    db.session.delete(proposal)
    db.session.commit()
    flash('Expense proposal deleted.', 'success')
    return redirect(url_for('expenses'))

# ─── Suggestions ─────────────────────────────────────────────────────────────

@app.route('/suggestions')
@login_required
def suggestions():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    q = Suggestion.query
    if category:
        q = q.filter_by(category=category)
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(Suggestion.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    categories = db.session.query(Suggestion.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('suggestions/list.html', items=items, categories=categories,
                           current_category=category, current_status=status)

@app.route('/suggestions/new', methods=['GET', 'POST'])
@login_required
def new_suggestion():
    from forms import SuggestionForm
    form = SuggestionForm()
    if form.validate_on_submit():
        suggestion = Suggestion(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            is_anonymous=form.is_anonymous.data,
            submitter_id=current_user.id,
        )
        db.session.add(suggestion)
        db.session.commit()
        flash('Suggestion submitted!', 'success')
        return redirect(url_for('suggestions'))
    return render_template('suggestions/new.html', form=form)

@app.route('/suggestions/<suggestion_id>')
@login_required
def view_suggestion(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    return render_template('suggestions/detail.html', suggestion=suggestion)

@app.route('/suggestions/<suggestion_id>/vote', methods=['POST'])
@login_required
def vote_suggestion(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    existing = SuggestionVote.query.filter_by(suggestion_id=suggestion_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'voted': False, 'count': suggestion.vote_count()})
    vote = SuggestionVote(suggestion_id=suggestion_id, user_id=current_user.id)
    db.session.add(vote)
    if suggestion.submitter_id != current_user.id:
        create_notification(suggestion.submitter_id, 'vote',
                            f'{current_user.username} upvoted your idea',
                            body=suggestion.title[:100],
                            link=f'/suggestions/{suggestion_id}')
    db.session.commit()
    return jsonify({'voted': True, 'count': suggestion.vote_count()})

@app.route('/suggestions/<suggestion_id>/status', methods=['POST'])
@login_required
@admin_required
def update_suggestion_status(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    new_status = request.form.get('status', 'open')
    suggestion.status = new_status
    db.session.commit()
    flash(f'Suggestion marked as {new_status}.', 'success')
    return redirect(url_for('view_suggestion', suggestion_id=suggestion_id))

@app.route('/suggestions/<suggestion_id>/delete', methods=['POST'])
@login_required
def delete_suggestion(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    if not current_user.is_admin and suggestion.submitter_id != current_user.id:
        abort(403)
    db.session.delete(suggestion)
    db.session.commit()
    flash('Suggestion deleted.', 'success')
    return redirect(url_for('suggestions'))

# ─── Jobs ─────────────────────────────────────────────────────────────────────

@app.route('/jobs')
@login_required
def jobs():
    listings = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).all()
    return render_template('jobs/list.html', listings=listings)

@app.route('/jobs/<job_id>')
@login_required
def view_job(job_id):
    job = JobListing.query.get_or_404(job_id)
    from forms import JobApplicationForm
    form = JobApplicationForm()
    if current_user.is_authenticated:
        form.applicant_name.data = form.applicant_name.data or current_user.username
        form.email.data = form.email.data or current_user.email
    already_applied = JobApplication.query.filter_by(job_id=job_id, user_id=current_user.id).first() if current_user.is_authenticated else None
    return render_template('jobs/detail.html', job=job, form=form, already_applied=already_applied)

@app.route('/jobs/<job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    job = JobListing.query.get_or_404(job_id)
    if not job.is_active:
        flash('This position is no longer accepting applications.', 'warning')
        return redirect(url_for('jobs'))
    already = JobApplication.query.filter_by(job_id=job_id, user_id=current_user.id).first()
    if already:
        flash('You have already applied for this position.', 'warning')
        return redirect(url_for('view_job', job_id=job_id))
    from forms import JobApplicationForm
    form = JobApplicationForm()
    if form.validate_on_submit():
        resume_path = save_upload(form.resume.data, 'resume') if form.resume.data and form.resume.data.filename else ''
        application = JobApplication(
            job_id=job_id,
            applicant_name=form.applicant_name.data,
            email=form.email.data,
            phone=form.phone.data,
            cover_letter=form.cover_letter.data,
            resume_path=resume_path,
            user_id=current_user.id,
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted! We will be in touch.', 'success')
        return redirect(url_for('jobs'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')
    return redirect(url_for('view_job', job_id=job_id))

# ─── Messaging ───────────────────────────────────────────────────────────────

@app.route('/messages')
@login_required
def inbox():
    sent = DirectMessage.query.filter_by(sender_id=current_user.id).all()
    received = DirectMessage.query.filter_by(receiver_id=current_user.id).all()
    partner_ids = set()
    for m in sent: partner_ids.add(m.receiver_id)
    for m in received: partner_ids.add(m.sender_id)
    partners = User.query.filter(User.id.in_(partner_ids)).all() if partner_ids else []
    all_users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    unread = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return render_template('messages/inbox.html', partners=partners, all_users=all_users, unread=unread)

@app.route('/messages/<user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    other = User.query.get(user_id)
    if not other:
        flash('User not found.', 'danger')
        return redirect(url_for('inbox'))
    if request.method == 'POST':
        is_ajax = request.form.get('ajax') == '1'
        text = request.form.get('text', '').strip()
        if not text:
            if is_ajax: return jsonify({'ok': False, 'error': 'Empty message'})
            return redirect(url_for('conversation', user_id=user_id))
        msg = DirectMessage(sender_id=current_user.id, receiver_id=user_id, text=text)
        db.session.add(msg)
        create_notification(user_id, 'message',
                            f'New message from {current_user.username}',
                            body=text[:100], link=f'/messages/{current_user.id}')
        db.session.commit()
        if is_ajax:
            return jsonify({'ok': True, 'message': {
                'id': msg.id, 'sender_id': msg.sender_id,
                'sender_username': current_user.username,
                'text': text, 'time': msg.created_at.strftime('%d %b %H:%M')
            }})
        return redirect(url_for('conversation', user_id=user_id))
    DirectMessage.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    msgs = DirectMessage.query.filter(
        ((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == user_id)) |
        ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == current_user.id))
    ).order_by(DirectMessage.created_at.asc()).all()
    return render_template('messages/conversation.html', other=other, messages=msgs)

@app.route('/messages/<user_id>/poll')
@login_required
def message_poll(user_id):
    after_id = request.args.get('after', '')
    other = User.query.get(user_id)
    if not other or not after_id:
        return jsonify({'messages': []})
    last = DirectMessage.query.get(after_id)
    if not last:
        return jsonify({'messages': []})
    msgs = DirectMessage.query.filter(
        ((DirectMessage.sender_id == current_user.id) & (DirectMessage.receiver_id == user_id)) |
        ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == current_user.id))
    ).filter(DirectMessage.created_at > last.created_at).order_by(DirectMessage.created_at.asc()).all()
    DirectMessage.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    result = [{'id': m.id, 'sender_id': m.sender_id,
               'sender_username': other.username if m.sender_id == user_id else current_user.username,
               'text': m.text, 'image_path': m.image_path or '',
               'time': m.created_at.strftime('%d %b %H:%M')} for m in msgs]
    return jsonify({'messages': result})

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def group_chat():
    if request.method == 'POST':
        is_ajax = request.form.get('ajax') == '1'
        text = request.form.get('text', '').strip()
        if not text:
            if is_ajax: return jsonify({'ok': False, 'error': 'Empty message'})
            return redirect(url_for('group_chat'))
        msg = GroupMessage(sender_id=current_user.id, text=text)
        db.session.add(msg)
        db.session.commit()
        if is_ajax:
            return jsonify({'ok': True, 'message': {
                'id': msg.id, 'sender_id': msg.sender_id,
                'sender_username': current_user.username,
                'text': text, 'image_path': msg.image_path or '',
                'time': msg.created_at.strftime('%d %b %H:%M')
            }})
        return redirect(url_for('group_chat'))
    msgs = GroupMessage.query.order_by(GroupMessage.created_at.asc()).all()
    return render_template('messages/group_chat.html', messages=msgs)

@app.route('/chat/poll')
@login_required
def group_poll():
    after_id = request.args.get('after', '')
    if after_id:
        last = GroupMessage.query.get(after_id)
        if last:
            msgs = GroupMessage.query.filter(GroupMessage.created_at > last.created_at)\
                       .order_by(GroupMessage.created_at.asc()).all()
        else:
            msgs = []
    else:
        msgs = []
    result = [{'id': m.id, 'sender_id': m.sender_id,
               'sender_username': m.sender.username,
               'text': m.text, 'image_path': m.image_path or '',
               'time': m.created_at.strftime('%d %b %H:%M')} for m in msgs]
    return jsonify({'messages': result})

# ─── Admin ────────────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    from forms import CompanyUpdateForm, JobListingForm
    update_form = CompanyUpdateForm()
    job_form = JobListingForm()
    users = User.query.order_by(User.created_at.desc()).all()
    pending_expenses = ExpenseProposal.query.filter_by(status='pending').all()
    pending_apps = JobApplication.query.filter_by(status='pending').count()
    updates_count = CompanyUpdate.query.count()
    suggestions_count = Suggestion.query.count()
    jobs_count = JobListing.query.count()
    recent_updates = CompanyUpdate.query.order_by(
        CompanyUpdate.is_pinned.desc(), CompanyUpdate.created_at.desc()
    ).limit(8).all()
    return render_template('admin/dashboard.html',
        users=users,
        pending_expenses=pending_expenses,
        pending_apps=pending_apps,
        updates_count=updates_count,
        suggestions_count=suggestions_count,
        jobs_count=jobs_count,
        recent_updates=recent_updates,
        update_form=update_form,
        job_form=job_form,
    )

@app.route('/admin/toggle-admin/<user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
        return redirect(url_for('admin_dashboard'))
    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin access {status} for {user.username}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get(user_id)
    if not user or user.id == current_user.id:
        flash('Cannot delete this user.', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/jobs')
@login_required
@admin_required
def admin_jobs():
    listings = JobListing.query.order_by(JobListing.created_at.desc()).all()
    return render_template('admin/jobs.html', listings=listings)

@app.route('/admin/jobs/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new_job():
    from forms import JobListingForm
    form = JobListingForm()
    if form.validate_on_submit():
        job = JobListing(
            title=form.title.data,
            department=form.department.data,
            description=form.description.data,
            requirements=form.requirements.data,
            salary_range=form.salary_range.data,
            location=form.location.data,
            job_type=form.job_type.data,
            is_active=form.is_active.data,
            created_by=current_user.id,
        )
        db.session.add(job)
        db.session.commit()
        flash('Job listing posted!', 'success')
        return redirect(url_for('admin_jobs'))
    return render_template('admin/new_job.html', form=form)

@app.route('/admin/jobs/<job_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_job(job_id):
    job = JobListing.query.get_or_404(job_id)
    from forms import JobListingForm
    form = JobListingForm(obj=job)
    if form.validate_on_submit():
        job.title = form.title.data
        job.department = form.department.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        job.salary_range = form.salary_range.data
        job.location = form.location.data
        job.job_type = form.job_type.data
        job.is_active = form.is_active.data
        db.session.commit()
        flash('Job updated!', 'success')
        return redirect(url_for('admin_jobs'))
    return render_template('admin/new_job.html', form=form, editing=True, job=job)

@app.route('/admin/jobs/<job_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_job(job_id):
    job = JobListing.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job listing deleted.', 'success')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/<job_id>/applications')
@login_required
@admin_required
def admin_job_applications(job_id):
    job = JobListing.query.get_or_404(job_id)
    status_filter = request.args.get('status', '')
    q = JobApplication.query.filter_by(job_id=job_id)
    if status_filter:
        q = q.filter_by(status=status_filter)
    applications = q.order_by(JobApplication.created_at.desc()).all()
    return render_template('admin/applications.html', job=job, applications=applications, status_filter=status_filter)

@app.route('/admin/applications/<app_id>/review', methods=['POST'])
@login_required
@admin_required
def admin_review_application(app_id):
    application = JobApplication.query.get_or_404(app_id)
    from forms import ApplicationReviewForm
    form = ApplicationReviewForm()
    if form.validate_on_submit():
        application.status = form.status.data
        application.review_notes = form.review_notes.data
        application.reviewer_id = current_user.id
        application.reviewed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Application {form.status.data}.', 'success')
    return redirect(url_for('admin_job_applications', job_id=application.job_id))

# ─── Notifications ────────────────────────────────────────────────────────────

@app.route('/notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(25).all()
    unread = sum(1 for n in notifs if not n.is_read)
    return jsonify({
        'unread': unread,
        'notifications': [{
            'id': n.id,
            'type': n.ntype,
            'title': n.title,
            'body': n.body,
            'link': n.link,
            'is_read': n.is_read,
            'time': n.created_at.strftime('%b %d, %H:%M')
        } for n in notifs]
    })

@app.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    data = request.get_json(silent=True) or {}
    nid = data.get('id')
    if nid:
        n = Notification.query.filter_by(id=nid, user_id=current_user.id).first()
        if n:
            n.is_read = True
    else:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


# ─── Groq AI Chat ─────────────────────────────────────────────────────────────

@app.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """Groq-powered AI assistant with live company context injected as system prompt."""
    try:
        data = request.get_json(silent=True) or {}
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        # Trim history to last 20 exchanges to stay within token limits
        messages = messages[-20:]

        # ── Gather live company context ────────────────────────────────────────
        all_members     = User.query.order_by(User.created_at.asc()).all()
        total_members   = len(all_members)
        admin_users     = [u for u in all_members if u.is_admin]
        active_jobs     = JobListing.query.filter_by(is_active=True).count()
        all_jobs        = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).limit(8).all()
        pending_exp     = ExpenseProposal.query.filter_by(status='pending').count()
        approved_exp    = ExpenseProposal.query.filter_by(status='approved').count()
        rejected_exp    = ExpenseProposal.query.filter_by(status='rejected').count()
        total_updates   = CompanyUpdate.query.count()
        open_suggestions= Suggestion.query.filter_by(status='open').count()
        pinned_updates  = CompanyUpdate.query.filter_by(is_pinned=True).order_by(
                            CompanyUpdate.created_at.desc()).limit(3).all()
        recent_updates  = CompanyUpdate.query.order_by(
                            CompanyUpdate.created_at.desc()).limit(8).all()
        all_suggestions = Suggestion.query.all()
        all_suggestions.sort(key=lambda s: s.vote_count(), reverse=True)
        top_suggestions = all_suggestions[:8]
        recent_msgs     = GroupMessage.query.order_by(GroupMessage.created_at.desc()).limit(15).all()
        recent_msgs     = list(reversed(recent_msgs))
        all_expenses    = ExpenseProposal.query.order_by(ExpenseProposal.created_at.desc()).limit(10).all()
        pending_apps    = JobApplication.query.filter_by(status='pending').count()
        all_roles       = Role.query.order_by(Role.position.asc()).all()
        total_chat_msgs = GroupMessage.query.count()

        # Current user context
        my_expenses     = ExpenseProposal.query.filter_by(submitter_id=current_user.id).all()
        my_suggestions  = Suggestion.query.filter_by(submitter_id=current_user.id).count()
        my_roles        = [ur.role_obj.name for ur in current_user.user_roles] if hasattr(current_user, 'user_roles') else []

        updates_summary = '\n'.join(
            f"  • [{u.category}] {u.title} (by {u.author.username}, {u.created_at.strftime('%b %d %Y')})\n    {u.content[:200]}"
            for u in recent_updates
        ) or '  (none yet)'

        suggestions_summary = '\n'.join(
            f"  • \"{s.title}\" — {s.vote_count()} votes, status: {s.status}"
            + (f" (by {s.submitter.username if not s.is_anonymous else 'Anonymous'})" )
            for s in top_suggestions
        ) or '  (none yet)'

        jobs_summary = '\n'.join(
            f"  • {j.title} [{j.department or j.job_type}] @ {j.location} — {j.salary_range}"
            for j in all_jobs
        ) or '  (none yet)'

        pinned_summary = '\n'.join(
            f"  • {u.title}: {u.content[:200]}"
            for u in pinned_updates
        ) or '  (none pinned)'

        admin_names = ', '.join(u.username for u in admin_users) or 'none'

        members_summary = '\n'.join(
            f"  • {u.username} ({'Admin' if u.is_admin else 'Member'})"
            + (f" — roles: {', '.join(ur.role_obj.name for ur in u.user_roles)}" if u.user_roles else '')
            + f" — joined {u.created_at.strftime('%b %Y')}"
            for u in all_members
        ) or '  (none)'

        chat_summary = '\n'.join(
            f"  [{m.created_at.strftime('%b %d %H:%M')}] {m.sender.username}: {m.text[:120]}"
            for m in recent_msgs
        ) or '  (no messages yet)'

        expenses_summary = '\n'.join(
            f"  • {e.title} by {e.submitter.username} — {e.currency} {e.amount:.2f} [{e.status}] ({e.created_at.strftime('%b %d')})"
            for e in all_expenses
        ) or '  (none yet)'

        roles_summary = '\n'.join(
            f"  • {r.name} (color: {r.color}, {r.member_count} member{'s' if r.member_count != 1 else ''})"
            for r in all_roles
        ) or '  (no roles created yet)'

        my_expenses_summary = '\n'.join(
            f"  • {e.title} — {e.currency} {e.amount:.2f} [{e.status}]"
            for e in my_expenses
        ) or '  (none submitted)'

        system_prompt = f"""You are Overdrive AI — the intelligent assistant built into the Overdrive company management portal. You are helpful, concise, and professional with full real-time knowledge of everything in the portal.

=== PORTAL OVERVIEW ===
Overdrive is an internal company management platform with:
- Company Updates (admin announcements) · Expense Proposals (submit & approve) · Ideas & Suggestions (vote-based)
- Job Openings (post & apply) · Direct Messages (1-on-1) · Team Chat (group) · Team directory
- Admin Panel: post updates, manage jobs, review expenses, manage team & roles

=== LIVE TEAM ({total_members} members) ===
Admins: {admin_names}
{members_summary}

=== ROLES & POSITIONS ===
{roles_summary}

=== COMPANY UPDATES ({total_updates} total) ===
Pinned:
{pinned_summary}

Recent:
{updates_summary}

=== EXPENSES ===
Pending: {pending_exp} | Approved: {approved_exp} | Rejected: {rejected_exp}
Recent expense proposals:
{expenses_summary}

=== IDEAS & SUGGESTIONS (open: {open_suggestions}) ===
{suggestions_summary}

=== JOB OPENINGS ({active_jobs} active, {pending_apps} pending applications) ===
{jobs_summary}

=== RECENT TEAM CHAT ({total_chat_msgs} total messages) ===
Last 15 messages:
{chat_summary}

=== ABOUT YOU (the current user) ===
Name: {current_user.username}
Email: {current_user.email}
Portal role: {'Admin' if current_user.is_admin else 'Team Member'}
Your custom roles: {', '.join(my_roles) if my_roles else 'none assigned'}
Member since: {current_user.created_at.strftime('%B %d, %Y')}
Your expenses:
{my_expenses_summary}
Your suggestions submitted: {my_suggestions}

=== WHAT YOU CAN DO ===
- Answer any question about the portal, team, updates, expenses, jobs, chat, roles
- Summarise, analyse, or compare any data you see above
- Help draft updates, expense descriptions, suggestion titles, or job descriptions
- Give navigation guidance ("go to /expenses to submit", "admins can post at /admin")
- Answer general work and productivity questions
- You CANNOT modify data directly — direct users to the relevant page

Be concise. Use bullet points for lists. Today's date context: {datetime.utcnow().strftime('%A, %B %d, %Y')}."""

        # ── Call Groq ──────────────────────────────────────────────────────────
        from groq import Groq
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'system', 'content': system_prompt}] + messages,
            temperature=0.65,
            max_tokens=1024,
        )

        reply = completion.choices[0].message.content
        return jsonify({'reply': reply, 'model': completion.model})

    except Exception as e:
        logger.error(f'Groq AI error: {e}')
        return jsonify({'error': str(e)}), 500


# ─── Team ────────────────────────────────────────────────────────────────────

@app.route('/team')
@login_required
def team():
    members = User.query.order_by(User.created_at.asc()).all()
    return render_template('team.html', members=members)

# ─── Roles ────────────────────────────────────────────────────────────────────

@app.route('/admin/roles')
@login_required
@admin_required
def admin_roles():
    roles = Role.query.order_by(Role.position.asc(), Role.created_at.asc()).all()
    members = User.query.order_by(User.username.asc()).all()
    return render_template('admin/roles.html', roles=roles, members=members)

@app.route('/admin/roles/create', methods=['POST'])
@login_required
@admin_required
def create_role():
    name  = request.form.get('name', '').strip()
    color = request.form.get('color', '#6b7280').strip()
    icon  = request.form.get('icon', 'fas fa-tag').strip()
    if not name:
        flash('Role name is required.', 'danger')
        return redirect(url_for('admin_roles'))
    if Role.query.filter_by(name=name).first():
        flash('A role with that name already exists.', 'warning')
        return redirect(url_for('admin_roles'))
    role = Role(name=name, color=color, icon=icon, created_by=current_user.id)
    db.session.add(role)
    db.session.commit()
    flash(f'Role "{name}" created.', 'success')
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/<role_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    name = role.name
    db.session.delete(role)
    db.session.commit()
    flash(f'Role "{name}" deleted.', 'success')
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/<role_id>/assign/<user_id>', methods=['POST'])
@login_required
@admin_required
def assign_role(role_id, user_id):
    Role.query.get_or_404(role_id)
    User.query.get_or_404(user_id)
    if not UserRole.query.filter_by(user_id=user_id, role_id=role_id).first():
        ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=current_user.id)
        db.session.add(ur)
        db.session.commit()
    return jsonify({'ok': True})

@app.route('/admin/roles/<role_id>/unassign/<user_id>', methods=['POST'])
@login_required
@admin_required
def unassign_role(role_id, user_id):
    ur = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
    if ur:
        db.session.delete(ur)
        db.session.commit()
    return jsonify({'ok': True})

# ─── Media Uploads ────────────────────────────────────────────────────────────

@app.route('/chat/upload', methods=['POST'])
@login_required
def chat_upload():
    file = request.files.get('image')
    if not file or not allowed_file(file.filename):
        return jsonify({'ok': False, 'error': 'Invalid file'}), 400
    image_path = save_upload(file, 'chat')
    text = request.form.get('text', '').strip()
    msg = GroupMessage(sender_id=current_user.id, text=text, image_path=image_path)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True, 'message': {
        'id': msg.id, 'sender_id': msg.sender_id,
        'sender_username': current_user.username,
        'text': text, 'image_path': image_path,
        'time': msg.created_at.strftime('%d %b %H:%M')
    }})

@app.route('/messages/<user_id>/upload', methods=['POST'])
@login_required
def message_upload(user_id):
    User.query.get_or_404(user_id)
    file = request.files.get('image')
    if not file or not allowed_file(file.filename):
        return jsonify({'ok': False, 'error': 'Invalid file'}), 400
    image_path = save_upload(file, 'dm')
    text = request.form.get('text', '').strip()
    msg = DirectMessage(sender_id=current_user.id, receiver_id=user_id,
                        text=text, image_path=image_path)
    db.session.add(msg)
    create_notification(user_id, 'message',
                        f'New message from {current_user.username}',
                        body='[Image]', link=f'/messages/{current_user.id}')
    db.session.commit()
    return jsonify({'ok': True, 'message': {
        'id': msg.id, 'sender_id': msg.sender_id,
        'sender_username': current_user.username,
        'text': text, 'image_path': image_path,
        'time': msg.created_at.strftime('%d %b %H:%M')
    }})

# ─── Energy Drink White-Label Store ──────────────────────────────────────────

@app.route('/store')
@login_required
def store():
    brand    = EnergyDrinkBrand.query.first()
    products = EnergyDrinkProduct.query.filter_by(is_active=True).order_by(EnergyDrinkProduct.name.asc()).all()
    return render_template('store/index.html', brand=brand, products=products)

@app.route('/admin/store')
@login_required
@admin_required
def admin_store():
    brand     = EnergyDrinkBrand.query.first()
    products  = EnergyDrinkProduct.query.order_by(EnergyDrinkProduct.name.asc()).all()
    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(60).all()
    return render_template('admin/store.html', brand=brand, products=products, movements=movements)

@app.route('/admin/store/brand', methods=['POST'])
@login_required
@admin_required
def admin_store_brand():
    brand = EnergyDrinkBrand.query.first()
    if not brand:
        brand = EnergyDrinkBrand(); db.session.add(brand)
    brand.brand_name    = request.form.get('brand_name', 'Overdrive Energy').strip()[:100]
    brand.tagline       = request.form.get('tagline', '').strip()[:200]
    brand.primary_color = request.form.get('primary_color', '#e63946').strip()[:7]
    brand.accent_color  = request.form.get('accent_color', '#ff6b35').strip()[:7]
    brand.website_url   = request.form.get('website_url', '').strip()[:255]
    brand.instagram_url = request.form.get('instagram_url', '').strip()[:255]
    brand.distributor   = request.form.get('distributor', '').strip()[:200]
    logo = request.files.get('logo')
    if logo and logo.filename and allowed_file(logo.filename):
        brand.logo_path = save_upload(logo, 'brand_logo')
    db.session.commit()
    flash('Brand settings saved!', 'success')
    return redirect(url_for('admin_store') + '?tab=brand')

@app.route('/admin/store/product/add', methods=['POST'])
@login_required
@admin_required
def admin_store_add_product():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Product name is required.', 'danger')
        return redirect(url_for('admin_store'))
    sku      = request.form.get('sku', '').strip() or None
    flavor   = request.form.get('flavor', 'Original').strip()
    size_ml  = int(request.form.get('size_ml', 0) or 0)
    price_c  = float(request.form.get('price_cost', 0) or 0)
    price_r  = float(request.form.get('price_retail', 0) or 0)
    stock_q  = int(request.form.get('stock_quantity', 0) or 0)
    min_stock= int(request.form.get('min_stock', 10) or 10)
    desc     = request.form.get('description', '').strip()
    ingr     = request.form.get('ingredients', '').strip()
    img      = request.files.get('image')
    img_path = save_upload(img, 'product') if img and img.filename and allowed_file(img.filename) else ''
    p = EnergyDrinkProduct(name=name, sku=sku, flavor=flavor, size_ml=size_ml,
                           price_cost=price_c, price_retail=price_r,
                           stock_quantity=stock_q, min_stock=min_stock,
                           image_path=img_path, description=desc, ingredients=ingr)
    db.session.add(p)
    db.session.flush()
    if stock_q > 0:
        db.session.add(StockMovement(product_id=p.id, quantity=stock_q,
                                     reason='initial', notes='Initial stock setup',
                                     created_by=current_user.id))
    db.session.commit()
    flash(f'Product "{name}" added.', 'success')
    return redirect(url_for('admin_store'))

@app.route('/admin/store/product/<product_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_store_edit_product(product_id):
    p = EnergyDrinkProduct.query.get_or_404(product_id)
    p.name         = request.form.get('name', p.name).strip()
    p.sku          = request.form.get('sku', p.sku or '').strip() or None
    p.flavor       = request.form.get('flavor', p.flavor).strip()
    p.size_ml      = int(request.form.get('size_ml', p.size_ml) or 0)
    p.price_cost   = float(request.form.get('price_cost', p.price_cost) or 0)
    p.price_retail = float(request.form.get('price_retail', p.price_retail) or 0)
    p.min_stock    = int(request.form.get('min_stock', p.min_stock) or 10)
    p.description  = request.form.get('description', p.description).strip()
    p.ingredients  = request.form.get('ingredients', p.ingredients).strip()
    p.is_active    = request.form.get('is_active') == 'on'
    img = request.files.get('image')
    if img and img.filename and allowed_file(img.filename):
        p.image_path = save_upload(img, 'product')
    db.session.commit()
    flash('Product updated.', 'success')
    return redirect(url_for('admin_store'))

@app.route('/admin/store/product/<product_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_store_delete_product(product_id):
    p = EnergyDrinkProduct.query.get_or_404(product_id)
    name = p.name
    db.session.delete(p)
    db.session.commit()
    flash(f'Product "{name}" deleted.', 'success')
    return redirect(url_for('admin_store'))

@app.route('/admin/store/product/<product_id>/stock', methods=['POST'])
@login_required
@admin_required
def admin_store_adjust_stock(product_id):
    p      = EnergyDrinkProduct.query.get_or_404(product_id)
    qty    = int(request.form.get('quantity', 0) or 0)
    reason = request.form.get('reason', 'manual').strip()
    notes  = request.form.get('notes', '').strip()
    batch  = request.form.get('batch_number', '').strip()
    if qty == 0:
        flash('Quantity cannot be zero.', 'warning')
        return redirect(url_for('admin_store'))
    p.stock_quantity = max(0, p.stock_quantity + qty)
    db.session.add(StockMovement(product_id=p.id, quantity=qty, reason=reason,
                                  notes=notes, batch_number=batch, created_by=current_user.id))
    db.session.commit()
    sign = f"+{qty}" if qty > 0 else str(qty)
    flash(f'Stock adjusted {sign} for {p.name}. New total: {p.stock_quantity}', 'success')
    return redirect(url_for('admin_store'))

@app.route('/admin/store/import', methods=['POST'])
@login_required
@admin_required
def admin_store_import():
    import csv, io
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid .csv file.', 'danger')
        return redirect(url_for('admin_store') + '?tab=import')
    text   = file.read().decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(text))
    added = skipped = 0
    for row in reader:
        name = (row.get('name') or '').strip()
        if not name: skipped += 1; continue
        sku = (row.get('sku') or '').strip() or None
        if sku and EnergyDrinkProduct.query.filter_by(sku=sku).first(): skipped += 1; continue
        p = EnergyDrinkProduct(
            name=name, sku=sku,
            flavor=(row.get('flavor') or 'Original').strip(),
            size_ml=int(row.get('size_ml') or 0),
            price_cost=float(row.get('price_cost') or 0),
            price_retail=float(row.get('price_retail') or 0),
            stock_quantity=int(row.get('stock_quantity') or 0),
            description=(row.get('description') or '').strip(),
        )
        db.session.add(p)
        db.session.flush()
        if p.stock_quantity > 0:
            db.session.add(StockMovement(product_id=p.id, quantity=p.stock_quantity,
                                          reason='import', notes='CSV import',
                                          created_by=current_user.id))
        added += 1
    db.session.commit()
    flash(f'Import complete: {added} product(s) added, {skipped} skipped.', 'success')
    return redirect(url_for('admin_store'))

@app.route('/admin/store/csv-template')
@login_required
@admin_required
def admin_store_csv_template():
    csv_content = ('name,sku,flavor,size_ml,price_cost,price_retail,stock_quantity,description\n'
                   'Overdrive Original,OD-001,Original,500,0.80,1.99,100,Classic energy drink\n'
                   'Overdrive Berry Blast,OD-002,Berry Blast,500,0.80,1.99,50,Berry flavoured variety\n'
                   'Overdrive Zero Sugar,OD-003,Zero Sugar,500,0.85,2.09,75,Sugar-free version\n')
    return Response(csv_content, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=overdrive_products_template.csv'})

# ─── Voice / Video Calls (Jitsi WebRTC) ──────────────────────────────────────

@app.route('/call/<room_id>')
@login_required
def call_room(room_id):
    import re
    room_id    = re.sub(r'[^a-zA-Z0-9\-_]', '', room_id)[:64]
    video_only = request.args.get('video', 'true') != 'false'
    return render_template('calls/room.html', room_id=room_id, video_only=video_only)

@app.route('/call/start/<user_id>', methods=['POST'])
@login_required
def call_start(user_id):
    other     = User.query.get_or_404(user_id)
    call_type = request.form.get('type', 'video')
    room_id   = f"od-{uuid.uuid4().hex[:20]}"
    call_url  = url_for('call_room', room_id=room_id, _external=False)
    emoji     = '📞' if call_type == 'voice' else '🎥'
    dm = DirectMessage(sender_id=current_user.id, receiver_id=user_id,
                       text=f"{emoji} {current_user.username} is calling you! Join: {call_url}")
    db.session.add(dm)
    create_notification(user_id, 'message',
                        f'{"Voice" if call_type=="voice" else "Video"} call from {current_user.username}',
                        body='Tap to join the call', link=call_url)
    db.session.commit()
    return jsonify({'ok': True, 'room_id': room_id, 'call_url': call_url})

# ─── Email Verification ───────────────────────────────────────────────────────

def send_email(to_email, subject, body_html):
    """Send email via SMTP. Set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in Replit Secrets."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    smtp_host = os.environ.get('MAIL_SERVER', '')
    smtp_port = int(os.environ.get('MAIL_PORT', '587'))
    smtp_user = os.environ.get('MAIL_USERNAME', '')
    smtp_pass = os.environ.get('MAIL_PASSWORD', '')
    mail_from = os.environ.get('MAIL_FROM', smtp_user)
    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.info(f'[MAIL] Not configured — would send to {to_email}: {subject}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = mail_from
        msg['To']      = to_email
        msg.attach(MIMEText(body_html, 'html'))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as srv:
            srv.starttls()
            srv.login(smtp_user, smtp_pass)
            srv.sendmail(mail_from, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f'[MAIL] Send error: {e}')
        return False

@app.route('/verify-email/<token>')
def verify_email(token):
    ev = EmailVerification.query.filter_by(token=token, is_used=False).first()
    if not ev:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('login'))
    if (datetime.utcnow() - ev.created_at).total_seconds() > 86400:
        flash('Verification link expired. Request a new one from your profile.', 'warning')
        return redirect(url_for('login'))
    ev.is_used = True
    db.session.commit()
    flash('✅ Email verified! You can now sign in.', 'success')
    return redirect(url_for('login'))

@app.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    EmailVerification.query.filter_by(user_id=current_user.id, is_used=False).update({'is_used': True})
    ev = EmailVerification(user_id=current_user.id)
    db.session.add(ev)
    db.session.commit()
    company     = ServerConfig.get('company_name', 'Overdrive')
    verify_url  = url_for('verify_email', token=ev.token, _external=True)
    html = f'''<div style="font-family:sans-serif;background:#0a0a0a;color:#f0f0f0;padding:40px;border-radius:12px;max-width:500px;">
        <h2 style="color:#e63946;margin-top:0;">⚡ {company}</h2>
        <p>Hi {current_user.username},</p>
        <p>Click below to verify your email address:</p>
        <a href="{verify_url}" style="display:inline-block;background:#e63946;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;margin:16px 0;">Verify Email</a>
        <p style="color:#666;font-size:12px;">Or copy: {verify_url}</p>
        <p style="color:#666;font-size:12px;">Link expires in 24 hours.</p></div>'''
    sent = send_email(current_user.email, f'Verify your {company} account', html)
    if sent:
        flash(f'Verification email sent to {current_user.email}.', 'success')
    else:
        flash('Email not configured. Set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in Replit Secrets.', 'warning')
    return redirect(url_for('profile'))

# ─── Misc ─────────────────────────────────────────────────────────────────────

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'app': 'Overdrive', 'timestamp': datetime.now().isoformat()})

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum 32MB.', 'danger')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
