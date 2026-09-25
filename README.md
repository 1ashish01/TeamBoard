# TeamBoard

TeamBoard is a Django REST API for an AI-powered Knowledge Base used by registered companies to search technical Q&A content.

## Features

* Company registration with automatic API key generation
* JWT authentication
* Role-based access (`ADMIN` / `CLIENT`)
* Knowledge Base search
* Query logging
* Admin usage summary
* Automated API tests

## Tech Stack

* Python
* Django
* Django REST Framework
* Simple JWT
* SQLite

## API Endpoints

| Method | Endpoint                    | Access     |
| ------ | --------------------------- | ---------- |
| POST   | `/api/auth/register/`       | Public     |
| POST   | `/api/auth/login/`          | Public     |
| POST   | `/api/kb/query/`            | JWT        |
| GET    | `/api/admin/usage-summary/` | Admin only |

## Setup

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Testing

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

## Authentication

Protected APIs use:

```text
Authorization: Bearer <access_token>
```

Company identity is taken from the authenticated user, not from the request body.

## Project Structure

```text
TeamBoard/
├── core/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py
│   ├── signals.py
│   ├── urls.py
│   └── tests.py
├── teamboard/
├── manage.py
├── requirements.txt
└── README.md
```
