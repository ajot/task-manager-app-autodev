"""
Authentication Views - Login, Register, Logout
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.models import User
from app import db
import requests
import json

auth_views_bp = Blueprint('auth_views', __name__, url_prefix='/auth')

@auth_views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and form handler"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Call backend API for authentication
        api_url = request.url_root + 'api/auth/login'
        response = requests.post(api_url, json={
            'email': email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            # Store tokens in session
            session['access_token'] = data['data']['access_token']
            session['refresh_token'] = data['data']['refresh_token']
            session['user'] = data['data']['user']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard_views.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@auth_views_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and form handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        # Call backend API for registration
        api_url = request.url_root + 'api/auth/register'
        response = requests.post(api_url, json={
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name
        })
        
        if response.status_code == 201:
            data = response.json()
            # Auto-login after registration
            session['access_token'] = data['data']['access_token']
            session['refresh_token'] = data['data']['refresh_token']
            session['user'] = data['data']['user']
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('dashboard_views.dashboard'))
        else:
            error_msg = response.json().get('error', 'Registration failed')
            flash(error_msg, 'danger')
    
    return render_template('auth/register.html')

@auth_views_bp.route('/logout')
def logout():
    """Logout user"""
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth_views.login'))