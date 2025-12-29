
import psycopg2
from psycopg2.extras import RealDictCursor
import os


def get_connection():
    """Crea e restituisce una connessione al database PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB', 'flask_db'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        return connection
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")
        return None


def init_db():
    """Inizializza il database creando le tabelle necessarie"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Crea tabella utenti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crea tabella posts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Database inizializzato con successo!")
        except Exception as e:
            print(f"Errore nell'inizializzazione del database: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()


# ===== QUERY UTENTI =====

def create_user(username, email):
    """Crea un nuovo utente (senza password - per compatibilità)"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING *",
                (username, email, 'default_hash')
            )
            user = cursor.fetchone()
            conn.commit()
            return dict(user)
        except Exception as e:
            print(f"Errore nella creazione dell'utente: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def create_user_with_password(username, email, password_hash):
    """Crea un nuovo utente con password"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING *",
                (username, email, password_hash)
            )
            user = cursor.fetchone()
            conn.commit()
            return dict(user)
        except Exception as e:
            print(f"Errore nella creazione utente: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def get_user_by_id(user_id):
    """Ottiene un utente per ID"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"Errore nel recupero dell'utente: {e}")
            return None
        finally:
            cursor.close()
            conn.close()


def get_all_users():
    """Ottiene tutti gli utenti"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            return [dict(user) for user in users]
        except Exception as e:
            print(f"Errore nel recupero degli utenti: {e}")
            return []
        finally:
            cursor.close()
            conn.close()


def update_user(user_id, username=None, email=None):
    """Aggiorna un utente"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if username and email:
                cursor.execute(
                    "UPDATE users SET username = %s, email = %s WHERE id = %s RETURNING *",
                    (username, email, user_id)
                )
            elif username:
                cursor.execute(
                    "UPDATE users SET username = %s WHERE id = %s RETURNING *",
                    (username, user_id)
                )
            elif email:
                cursor.execute(
                    "UPDATE users SET email = %s WHERE id = %s RETURNING *",
                    (email, user_id)
                )
            else:
                return None
            
            user = cursor.fetchone()
            conn.commit()
            return dict(user) if user else None
        except Exception as e:
            print(f"Errore nell'aggiornamento dell'utente: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()


def delete_user(user_id):
    """Elimina un utente"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Errore nell'eliminazione dell'utente: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()


# ===== QUERY POSTS =====

def create_post(user_id, title, content):
    """Crea un nuovo post"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s) RETURNING *",
                (user_id, title, content)
            )
            post = cursor.fetchone()
            conn.commit()
            return dict(post)
        except Exception as e:
            print(f"Errore nella creazione del post: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()


def get_post_by_id(post_id):
    """Ottiene un post per ID"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT p.*, u.username 
                FROM posts p 
                JOIN users u ON p.user_id = u.id 
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            return dict(post) if post else None
        except Exception as e:
            print(f"Errore nel recupero del post: {e}")
            return None
        finally:
            cursor.close()
            conn.close()


def get_all_posts():
    """Ottiene tutti i posts"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT p.*, u.username 
                FROM posts p 
                JOIN users u ON p.user_id = u.id 
                ORDER BY p.created_at DESC
            """)
            posts = cursor.fetchall()
            return [dict(post) for post in posts]
        except Exception as e:
            print(f"Errore nel recupero dei posts: {e}")
            return []
        finally:
            cursor.close()
            conn.close()


def get_posts_by_user(user_id):
    """Ottiene tutti i posts di un utente"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM posts 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            posts = cursor.fetchall()
            return [dict(post) for post in posts]
        except Exception as e:
            print(f"Errore nel recupero dei posts dell'utente: {e}")
            return []
        finally:
            cursor.close()
            conn.close()


def delete_post(post_id):
    """Elimina un post"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Errore nell'eliminazione del post: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def get_user_by_username(username):
    """Ottiene un utente per username"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"Errore nel recupero dell'utente: {e}")
            return None
        finally:
            cursor.close()
            conn.close()