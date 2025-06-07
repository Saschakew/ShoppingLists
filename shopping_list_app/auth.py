from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User # Import from models.py instead of app.py

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) # Assuming a 'main' blueprint for dashboard
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Always remember the user for persistent login
            login_user(user, remember=True, duration=31536000)  # 1 year duration
            # Set session to permanent
            session.permanent = True
            flash('Logged in successfully!', category='success')
            # Redirect to a dashboard or home page after login
            return redirect(url_for('main.dashboard')) # Or some other appropriate page
        else:
            flash('Login Unsuccessful. Please check username and password', category='danger')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different one.', category='warning')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match!', category='danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            username=username, 
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', category='success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/logout')
@login_required # Ensure user is logged in to logout
def logout():
    logout_user()
    flash('You have been logged out.', category='info')
    return redirect(url_for('auth.login'))
