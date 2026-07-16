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
    JobListing, JobApplication, ServerConfig
)

with app.app_context():
    db.create_all()
    if not ServerConfig.query.filter_by(key='company_name').first():
        ServerConfig.set('company_name', 'Overdrive')

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

@app.context_processor
def inject_globals():
    unread = 0
    if current_user.is_authenticated:
        try:
            unread = DirectMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        except Exception:
            pass
    return dict(unread_count=unread, now=datetime.utcnow())

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
    return render_template('auth/register.html', form=form)

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
    return render_template('auth/login.html', form=form)

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
               'text': m.text, 'time': m.created_at.strftime('%d %b %H:%M')} for m in msgs]
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
                'text': text, 'time': msg.created_at.strftime('%d %b %H:%M')
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
               'text': m.text, 'time': m.created_at.strftime('%d %b %H:%M')} for m in msgs]
    return jsonify({'messages': result})

# ─── Admin ────────────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    pending_expenses = ExpenseProposal.query.filter_by(status='pending').all()
    pending_apps = JobApplication.query.filter_by(status='pending').count()
    updates_count = CompanyUpdate.query.count()
    suggestions_count = Suggestion.query.count()
    jobs_count = JobListing.query.count()
    return render_template('admin/dashboard.html',
        users=users,
        pending_expenses=pending_expenses,
        pending_apps=pending_apps,
        updates_count=updates_count,
        suggestions_count=suggestions_count,
        jobs_count=jobs_count,
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
