# Social Media REST API

A social media REST API built with FastAPI. Users can register, log in, create posts, comment on posts, like posts, and retrieve posts with sorting options.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | SQLite (async via aiosqlite) |
| ORM | SQLAlchemy + databases |
| Auth | JWT Bearer tokens (HS256) |
| Validation | Pydantic v2 |
| Password Hashing | bcrypt |
| Testing | pytest + httpx (async) |
| Logging | RichHandler + rotating file + Logtail |

---

## Project Structure

```
REST_API/
├── .env                    # Environment variables
├── .env.example            # Env variable template
├── data.db                 # Development SQLite database
├── socialapi/
│   ├── main.py             # App setup, middleware, lifespan
│   ├── config.py           # Dev/Prod/Test environment config
│   ├── database.py         # Table definitions and DB connection
│   ├── security.py         # JWT, bcrypt, OAuth2 logic
│   ├── logging_conf.py     # Logging setup with email obfuscation
│   ├── models/
│   │   ├── user.py         # User, UserIn
│   │   └── post.py         # Post, Comment, Like models
│   ├── routers/
│   │   ├── user.py         # /register, /token
│   │   └── post.py         # /post, /comment, /like
│   └── test/
│       ├── conftest.py     # Shared fixtures
│       └── routers/
│           ├── test_user.py
│           └── test_post.py
```

---

## Database Schema

```
users
├── id (PK)
├── email (unique)
└── password (hashed)

posts
├── id (PK)
├── body
└── user_id (FK → users.id)

comments
├── id (PK)
├── body
├── post_id (FK → posts.id)
└── user_id (FK → users.id)

likes
├── id (PK)
├── post_id (FK → posts.id)
└── user_id (FK → users.id)
```

---

## Endpoints

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register a new user |
| POST | `/token` | No | Login and receive a JWT token |

**Register body:**
```json
{ "email": "user@example.com", "password": "yourpassword" }
```

**Login body (form-encoded):**
```
username=user@example.com&password=yourpassword
```

**Token response:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### Posts

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/post` | Yes | Create a new post |
| GET | `/post` | No | Get all posts (with optional sorting) |
| GET | `/post/{post_id}` | No | Get a post with its comments and like count |

**Sorting options** (`?sorting=new` / `old` / `most_likes`):
```
GET /post?sorting=most_likes
```

---

### Comments

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/comment` | Yes | Create a comment on a post |
| GET | `/post/{post_id}/comment` | No | Get all comments for a post |

---

### Likes

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/like` | Yes | Like a post |

---

## Authentication

Protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after **15 minutes**. On expiry the API returns `401 Unauthorized` with `"Token expired"` in the detail.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
ENV_STATE=dev
DEV_DATABASE_URL=sqlite:///data.db
DEV_LOGTAIL_API_KEY=your_logtail_key
```

For production, use `PROD_DATABASE_URL` and `PROD_LOGTAIL_API_KEY`.

---

## Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn socialapi.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

---

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use a separate `test.db` with automatic rollback between each test so the database is always clean.

---

## Logging

- **Console**: Rich-formatted output with correlation IDs and email obfuscation
- **File**: Rotating file (`socialapi.log`, max 1MB, 5 backups) in JSON format
- **Remote**: Logtail integration for production log aggregation

Email addresses in logs are partially masked for privacy (first 2 chars shown in dev, 0 in prod).
