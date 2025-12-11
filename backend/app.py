from flask import Flask, jsonify, request, session, render_template
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import time
import database as db
import os 

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
    return jsonify({
        'message': 'Benvenuto nella Mini Flask App!',
        'endpoints': {
            'users': '/users',
            'posts': '/posts'
        }
    })


# ===== ROUTES AUTENTICAZIONE =====

app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email e spassword sono richieste!'}), 400

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

@app.route('/login', methods=['POST'])
def login():
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
