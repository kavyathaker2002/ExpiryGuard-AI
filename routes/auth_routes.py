import functools
from urllib.parse import urlsplit
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, seed_demo_inventory
from translations import get_text

auth_bp = Blueprint('auth', __name__)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    current_lang = session.get('lang', 'en')
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        preferred_lang = request.form.get('preferred_language', current_lang)

        if not shop_name or not username or not password:
            flash(get_text('error', current_lang) + ': Please fill all required fields.', 'danger')
            return render_template('auth/register.html', shop_name=shop_name, username=username)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', shop_name=shop_name, username=username)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html', shop_name=shop_name)

        pw_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (shop_name, username, password_hash, preferred_language) VALUES (?, ?, ?, ?)",
            (shop_name, username, pw_hash, preferred_lang)
        )
        new_user_id = cursor.lastrowid
        # Seed initial demo items so the new shopkeeper has sample data to explore
        seed_demo_inventory(cursor, new_user_id)
        db.commit()

        session.clear()
        session['user_id'] = new_user_id
        session['shop_name'] = shop_name
        session['username'] = username
        session['lang'] = preferred_lang

        flash(f'Welcome, {shop_name}! Your shop account is ready.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    current_lang = session.get('lang', 'en')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('auth/login.html', username=username)

        session.clear()
        session['user_id'] = user['id']
        session['shop_name'] = user['shop_name']
        session['username'] = user['username']
        session['lang'] = user['preferred_language'] or 'en'

        next_page = request.args.get('next', '')
        parsed_next = urlsplit(next_page)
        if parsed_next.scheme or parsed_next.netloc or not next_page.startswith('/') or next_page.startswith('//'):
            next_page = ''
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    lang = session.get('lang', 'en')
    session.clear()
    session['lang'] = lang
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        preferred_lang = request.form.get('preferred_language', 'en')
        new_password = request.form.get('new_password', '')
        
        if not shop_name:
            flash('Shop name cannot be empty.', 'danger')
        else:
            if new_password:
                pw_hash = generate_password_hash(new_password)
                cursor.execute(
                    "UPDATE users SET shop_name = ?, preferred_language = ?, password_hash = ? WHERE id = ?",
                    (shop_name, preferred_lang, pw_hash, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET shop_name = ?, preferred_language = ? WHERE id = ?",
                    (shop_name, preferred_lang, user_id)
                )
            db.commit()
            session['shop_name'] = shop_name
            session['lang'] = preferred_lang
            flash(get_text('profile_saved_msg', preferred_lang), 'success')
            
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/api/set-language', methods=['POST'])
def set_language():
    data = request.get_json(silent=True) or {}
    lang = data.get('lang', 'en')
    if lang not in ['en', 'hi', 'mr']:
        lang = 'en'
    session['lang'] = lang
    
    if 'user_id' in session:
        try:
            db = get_db()
            db.execute("UPDATE users SET preferred_language = ? WHERE id = ?", (lang, session['user_id']))
            db.commit()
        except Exception:
            pass
            
    return jsonify({"success": True, "lang": lang})
