from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, RegistrationForm
from .models import db, User

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('landing_page.html', title='Welcome')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # Check if this is the first user
        if User.query.count() == 0:
            user.is_admin = True
            # Try to assign 'Ultimate+' plan
            from .models import Plan # Import Plan model
            ultimate_plan = Plan.query.filter_by(name='Ultimate+').first()
            if ultimate_plan:
                user.plan_id = ultimate_plan.id
                flash('Welcome, Admin! You have been granted the Ultimate+ plan.')
            else:
                flash('Welcome, Admin! Admin rights granted. The "Ultimate+" plan was not found yet.')
        else:
            flash('Congratulations, you are now a registered user!')

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('signup.html', title='Sign Up', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!')
        # Redirect to the page requested before login, or to index
        next_page = request.args.get('next')
        if not next_page:
            next_page = url_for('main.dashboard')
        else:
            # Ensure the URL is local to the application
            # urlparse from urllib.parse
            next_page_netloc = urlparse(next_page).netloc
            if next_page_netloc and next_page_netloc != urlparse(request.host_url).netloc:
                flash("Redirect URL is not valid.")
                next_page = url_for('main.dashboard') # or redirect to login again
            elif not next_page.startswith('/') and not next_page_netloc: # Relative path without leading slash, can be tricky.
                # For simplicity, if it's not starting with / and has no netloc, assume it's a local view name
                # This might need more robust handling for complex cases
                pass # Assume it's a valid relative path like 'main.dashboard' or just 'dashboard'
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

@bp.route('/pricing')
def pricing():
    # In a future step, you might query plans from the database here
    # plans = Plan.query.all()
    # return render_template('prices_page.html', title='Pricing', plans=plans)
    return render_template('prices_page.html', title='Pricing Plans')

# Need to import request for the next_page logic in login
from flask import request
from urllib.parse import urlparse
