# Arhan Financial Platform 🏦

A scalable, event-driven banking platform built using Django and a Microservices Architecture. The system simulates core banking operations including account management, secure funds transfer (via transfers, card payments or loans), card processing, and double-entry bookkeeping, orchestrated via an Nginx API Gateway.

🚀 Key Architecture

The project is split into five decoupled services that communicate asynchronously using RabbitMQ and Celery:

🔐 Identity Service: The centralized authentication authority. It handles user registration, JWT issuance (with custom claim enrichment), and Role-Based Access Control (RBAC) for Customers and Staff.

💰 Account Service: The core banking engine. It manages account lifecycles (Savings/Current), loan processing, support ticketing, and enforces balance consistency.

💸 Payment Service: The transaction orchestrator. It executes internal transfers and card charges, utilizing atomic transactions and connection pooling to ensure financial accuracy across distributed databases.

📖 Ledger Service: An immutable audit log. Acting as a passive consumer, it listens for finalized transaction events to record double-entry bookkeeping records, ensuring eventual consistency and data integrity.

💻 Frontend Service: A user-facing web portal acting as a Backend-for-Frontend (BFF). It aggregates data from multiple microservices into a unified UI, handling session management and secure token storage.


🛠️ Tech Stack

Framework: Python, Django, Django Rest Framework (DRF)

Infrastructure: Nginx (Gateway), RabbitMQ (Message Broker), Celery (Workers)

Gateway: Nginx (Reverse Proxy)

Security:

Auth: JWT with Service-to-Service validation.

Encryption: Fernet (Symmetric Encryption) for sensitive card data.

Hashing: PBKDF2 (NIST compliant) for credentials.

Database: Distributed SQL Databases (per service)


## Run Locally

Clone the project

```bash
  git clone https://github.com/Daneil98/arhan_financial
```

Go to each microservice project directory and do the following:

```bash
  cd arhan_financial
```

```bash
  cd "microservice_project_name" (e.g payments)
```

Install dependencies

```bash
  pip install -r Requirement.txt
```

Prepare for migrations

```bash
  python manage.py makemigrations
```

Enact migrations

```bash
  python manage.py migrate
```

Start the server

```bash
  python manage.py runserver
```

Start the celery worker. For example (Replace payment with the microservice app_name and payments with the microservice project name):

```bash
  celery -A payments worker -Q payment.internal -l info
```



## Environment Variables (For Each Microservice settings.py)
DEBUG=True (Set To False for Production)
SECRET_KEY=change_this_to_a_unique_random_string_per_service
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

### Database (Auto-overwritten by Render, used for Local Docker)
DATABASE_URL=sqlite:///db.sqlite3 

### Async Messaging (RabbitMQ)
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672/

### Security (MUST BE IDENTICAL ACROSS ALL SERVICES)
Generate via: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SHARED_SECRET=your-secure-shared-key-must-match-everywhere