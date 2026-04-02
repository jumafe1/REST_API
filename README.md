# Social Media REST API

A social media REST API built with FastAPI. Users register with email confirmation, log in with JWT tokens, create posts, comment, like posts, and retrieve posts with sorting options.

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
| Email | Mailgun (via httpx, background tasks) |
| File Storage | Backblaze B2 (b2sdk) |
| Testing | pytest + httpx (async) |
| Logging | RichHandler + rotating file + Logtail |

---

## Project Structure

```
REST_API/
├── .env                        # Environment variables
├── .env.example                # Env variable template
├── data.db                     # Development SQLite database
├── requirements.txt
├── requirements-dev.txt
└── socialapi/
    ├── main.py                 # App setup, middleware, lifespan
    ├── config.py               # Dev/Prod/Test environment config
    ├── database.py             # Table definitions and DB connection
    ├── security.py             # JWT, bcrypt, OAuth2 logic
    ├── task.py                 # Background tasks (email via Mailgun)
    ├── logging_conf.py         # Logging setup with email obfuscation
    ├── libs/
    │   └── b2/                 # Backblaze B2 file storage integration
    ├── models/
    │   ├── user.py             # User, UserIn
    │   └── post.py             # Post, Comment, Like models
    ├── routers/
    │   ├── user.py             # /register, /token, /confirm/{token}
    │   └── post.py             # /post, /comment, /like
    └── test/
        ├── conftest.py         # Shared fixtures
        ├── test_security.py
        ├── test_task.py
        └── routers/
            ├── test_user.py
            └── test_post.py
```

---

## Database Schema

```
users
├── id        (PK)
├── email     (unique)
├── password  (bcrypt hashed)
└── confirmed (bool, default false)

posts
├── id       (PK)
├── body
└── user_id  (FK → users.id)

comments
├── id       (PK)
├── body
├── post_id  (FK → posts.id)
└── user_id  (FK → users.id)

likes
├── id       (PK)
├── post_id  (FK → posts.id)
└── user_id  (FK → users.id)
```

---

## Endpoints

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register a new user (sends confirmation email) |
| GET | `/confirm/{token}` | No | Confirm email address via token |
| POST | `/token` | No | Login and receive a JWT (requires confirmed email) |

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

> Login will return `401` if the user has not confirmed their email.

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

Tokens expire after **15 minutes**. On expiry the API returns `401 Unauthorized` with `"Token has expired"` in the detail.

### Email Confirmation Flow

1. `POST /register` — creates the user and sends a confirmation email via Mailgun (background task)
2. User clicks the link in the email → `GET /confirm/{token}`
3. `POST /token` — login is only allowed after confirmation

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
ENV_STATE=dev

DEV_DATABASE_URL=sqlite:///data.db
DEV_LOGTAIL_API_KEY=your_logtail_key
DEV_MAILGUN_DOMAIN=your_mailgun_domain
DEV_MAILGUN_API_KEY=your_mailgun_api_key
DEV_B2_KEY_ID=your_b2_key_id
DEV_B2_APPLICATION_KEY=your_b2_application_key
DEV_B2_BUCKET_NAME=your_b2_bucket_name
```

For production, prefix all variables with `PROD_` instead of `DEV_`.

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

Tests use a separate `test.db` with automatic rollback between each test so the database is always clean. Mailgun HTTP calls are mocked via `pytest-mock` — no real emails are sent during tests.

---

## Logging

- **Console**: Rich-formatted output with correlation IDs and email obfuscation
- **File**: Rotating file (`socialapi.log`, max 1MB, 5 backups) in JSON format
- **Remote**: Logtail integration for production log aggregation

Email addresses in logs are partially masked for privacy (first 2 chars shown in dev, 0 in prod).
