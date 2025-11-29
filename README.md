# Mini Flask App con PostgreSQL

Una semplice applicazione Flask con database PostgreSQL gestita tramite Docker.

## Struttura

- **app.py**: Applicazione Flask con API REST per utenti e posts
- **database.py**: Query principali per PostgreSQL (CRUD operations)
- **docker-compose.yml**: Configurazione Docker per Flask e PostgreSQL
- **requirements.txt**: Dipendenze Python

## Avvio

1. Assicurati di avere Docker installato
2. Avvia l'applicazione:

```bash
docker-compose up --build
```

3. L'app sarà disponibile su: http://localhost:5000

## Endpoints API

### Utenti
- `GET /users` - Lista tutti gli utenti
- `POST /users` - Crea un nuovo utente
  ```json
  {
    "username": "mario",
    "email": "mario@example.com"
  }
  ```
- `GET /users/<id>` - Dettagli utente
- `PUT /users/<id>` - Aggiorna utente
- `DELETE /users/<id>` - Elimina utente

### Posts
- `GET /posts` - Lista tutti i posts
- `POST /posts` - Crea un nuovo post
  ```json
  {
    "user_id": 1,
    "title": "Titolo",
    "content": "Contenuto del post"
  }
  ```
- `GET /posts/<id>` - Dettagli post
- `DELETE /posts/<id>` - Elimina post
- `GET /users/<id>/posts` - Posts di un utente

## Esempi di utilizzo

```bash
# Crea un utente
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"mario","email":"mario@example.com"}'

# Lista utenti
curl http://localhost:5000/users

# Crea un post
curl -X POST http://localhost:5000/posts \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"title":"Primo post","content":"Contenuto interessante"}'
```

## Stop

```bash
docker-compose down
```

Per eliminare anche i dati del database:
```bash
docker-compose down -v
```
