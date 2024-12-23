from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, db

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'error')
            return redirect(url_for('auth.signup'))
        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'error')
            return redirect(url_for('auth.signup'))

        # Create new user
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Verify user
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'error')

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
