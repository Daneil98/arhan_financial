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
CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = 'json'

CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = 'UTC'

CELERY_ACKS_LATE = True   # ensures tasks are not lost if worker crashes

CELERY_TASK_REJECT_ON_WORKER_LOST = True

CELERY_TASK_TRACK_STARTED = True

CELERY_BROKER_URL = ''  (e.g amqp://guest:guest@localhost:5672/)

CELERY_TASK_DEFAULT_QUEUE = ''  (e.g account_service_internal)

JWT_SHARED_SECRET = '' (e.g 'your-very-long-and-secure-shared-jwt-secret-key-0987654321')

ENCRYPTION_KEY = '' (Generate a Fernet Encryption key for account_services)
