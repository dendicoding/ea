from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import time
import backend.database as db
import os 
import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.before_request
def before_first_request():
    """Inizializza il database al primo avvio"""
    if not hasattr(app, 'db_initialized'):
        time.sleep(3)  # Attende che PostgreSQL sia pronto
        db.init_db()
        app.db_initialized = True


@app.route('/')
def home():
    # Se l'utente è loggato, vai al calendario
    if session.get('user_id'):
        return redirect(url_for('calendar'))
    # Altrimenti vai al login
    return redirect(url_for('login'))


@app.route('/calendar')
def calendar():
    # Proteggi la route: solo utenti loggati
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    return render_template('calendar.html')


@app.route('/search')
def search():
    # Proteggi la route: solo utenti loggati
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    return render_template('search.html')


# ===== ROUTES AUTENTICAZIONE =====

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Se già loggato, vai al calendario
    if session.get('user_id'):
        return redirect(url_for('calendar'))
    
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email e password sono richieste!'}), 400

    # Controllo se l'utente già esiste
    existing_user = db.get_user_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username già esistente'}), 400
    
    # Hash della password
    password_hash = generate_password_hash(password)

    # Crea utente
    user = db.create_user_with_password(username, email, password_hash)
    if user:
        session['user_id'] = user['id']
        return jsonify({
            'message' : 'registrazione riuscita',
            'user' : {'id': user['id'], 'username': user['username'], 'email': user['email']}  
        }), 201
    return jsonify({'error' : 'Errore nella registrazione'}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se già loggato, vai al calendario
    if session.get('user_id'):
        return redirect(url_for('calendar'))
    
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.json
    username = data.get('username') 
    password = data.get('password')

    if not username or not password:
        return jsonify({'error' : 'Username e password sono richiesti'}), 400    
    
    user = db.get_user_by_username(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error' : 'Username o password non validi'}), 401
    
    session['user_id'] = user['id']
    return jsonify({
        'message': 'Login riuscito',
        'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
    }), 200

@app.route('/current-user', methods=['GET'])
def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error' : 'Non autenticato'}), 401
    
    user = db.get_user_by_id(user_id)
    if user:
        return jsonify(user), 200
    return jsonify({'error' : 'Utente non trovato'}), 404

# ===== ROUTES UTENTI =====

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        users = db.get_all_users()
        return jsonify(users)
    
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return jsonify({'error': 'Username e email sono richiesti'}), 400
        
        user = db.create_user(username, email)
        if user:
            return jsonify(user), 201
        return jsonify({'error': 'Errore nella creazione dell\'utente'}), 500

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = db.get_user_by_id(user_id)
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=user)


@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    oggi = datetime.datetime.now()
    user = db.get_user_by_id(user_id)
    if not user:
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=user, oggi=oggi)


@app.route('/users/<int:user_id>/change-password', methods=['POST'])
def change_password(user_id):
    # Verifica che l'utente stia modificando la propria password
    if session.get('user_id') != user_id:
        return jsonify({'error': 'Non autorizzato'}), 403
    
    data = request.json
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Password attuale e nuova password sono richieste'}), 400
    
    # Verifica password attuale
    user = db.get_user_by_id(user_id)
    if not user or not check_password_hash(user['password'], current_password):
        return jsonify({'error': 'Password attuale non corretta'}), 401
    
    # Aggiorna password
    new_password_hash = generate_password_hash(new_password)
    success = db.update_user_password(user_id, new_password_hash)
    
    if success:
        return jsonify({'message': 'Password aggiornata con successo'}), 200
    return jsonify({'error': 'Errore nell\'aggiornamento della password'}), 500


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(user_id):
    if request.method == 'GET':
        user = db.get_user_by_id(user_id)
        if user:
            return jsonify(user)
        return jsonify({'error': 'Utente non trovato'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        user = db.update_user(user_id, username, email)
        if user:
            return jsonify(user)
        return jsonify({'error': 'Errore nell\'aggiornamento dell\'utente'}), 500
    
    elif request.method == 'DELETE':
        if db.delete_user(user_id):
            return jsonify({'message': 'Utente eliminato con successo'})
        return jsonify({'error': 'Errore nell\'eliminazione dell\'utente'}), 500


# ===== ROUTES POSTS =====

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'GET':
        posts = db.get_all_posts()
        return jsonify(posts)
    
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        title = data.get('title')
        content = data.get('content')
        
        if not user_id or not title:
            return jsonify({'error': 'user_id e title sono richiesti'}), 400
        
        post = db.create_post(user_id, title, content)
        if post:
            return jsonify(post), 201
        return jsonify({'error': 'Errore nella creazione del post'}), 500


@app.route('/posts/<int:post_id>', methods=['GET', 'DELETE'])
def post_detail(post_id):
    if request.method == 'GET':
        post = db.get_post_by_id(post_id)
        if post:
            return jsonify(post)
        return jsonify({'error': 'Post non trovato'}), 404
    
    elif request.method == 'DELETE':
        if db.delete_post(post_id):
            return jsonify({'message': 'Post eliminato con successo'})
        return jsonify({'error': 'Errore nell\'eliminazione del post'}), 500


@app.route('/users/<int:user_id>/posts', methods=['GET'])
def user_posts(user_id):
    posts = db.get_posts_by_user(user_id)
    return jsonify(posts)


# ===== ROUTES PRENOTAZIONI =====

@app.route('/bookings', methods=['GET', 'POST'])
def bookings():
    if request.method == 'GET':
        # Ottieni tutte le prenotazioni o filtra per date
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            bookings = db.get_bookings_by_date_range(start_date, end_date)
        else:
            bookings = db.get_all_bookings()
        
        # Serializza le date per JSON
        for booking in bookings:
            if booking.get('booking_date'):
                booking['booking_date'] = booking['booking_date'].isoformat()
            if booking.get('start_time'):
                booking['start_time'] = str(booking['start_time'])
            if booking.get('end_time'):
                booking['end_time'] = str(booking['end_time'])
            if booking.get('created_at'):
                booking['created_at'] = booking['created_at'].isoformat()
        
        return jsonify(bookings)
    
    elif request.method == 'POST':
        # Solo utenti autenticati possono prenotare
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Devi essere autenticato per prenotare'}), 401
        
        data = request.json
        booking_date = data.get('booking_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        title = data.get('title')
        description = data.get('description')
        
        if not booking_date or not start_time or not title:
            return jsonify({'error': 'Data, ora inizio e titolo sono richiesti'}), 400
        
        # Verifica disponibilità
        if not db.check_slot_available(booking_date, start_time):
            return jsonify({'error': 'Questo slot è già occupato'}), 409
        
        # Crea prenotazione
        booking = db.create_booking(user_id, booking_date, start_time, end_time, title, description)
        if booking:
            # Serializza le date per JSON
            if booking.get('booking_date'):
                booking['booking_date'] = booking['booking_date'].isoformat()
            if booking.get('start_time'):
                booking['start_time'] = str(booking['start_time'])
            if booking.get('end_time'):
                booking['end_time'] = str(booking['end_time'])
            if booking.get('created_at'):
                booking['created_at'] = booking['created_at'].isoformat()
            
            return jsonify(booking), 201
        return jsonify({'error': 'Errore nella creazione della prenotazione'}), 500


@app.route('/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autenticato'}), 401
    
    if db.delete_booking(booking_id, user_id):
        return jsonify({'message': 'Prenotazione eliminata con successo'})
    return jsonify({'error': 'Errore nell\'eliminazione o prenotazione non trovata'}), 500


@app.route('/users/<int:user_id>/bookings', methods=['GET'])
def user_bookings(user_id):
    bookings = db.get_bookings_by_user(user_id)
    
    # Serializza le date per JSON
    for booking in bookings:
        if booking.get('booking_date'):
            booking['booking_date'] = booking['booking_date'].isoformat()
        if booking.get('start_time'):
            booking['start_time'] = str(booking['start_time'])
        if booking.get('end_time'):
            booking['end_time'] = str(booking['end_time'])
        if booking.get('created_at'):
            booking['created_at'] = booking['created_at'].isoformat()
    
    return jsonify(bookings)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
