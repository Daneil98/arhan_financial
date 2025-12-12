# Arhan Financial Platform 🏦

A scalable, event-driven banking backend built using Django and a Microservices Architecture. The system simulates core banking operations including account management, secure funds transfer, card processing, and double-entry bookkeeping, orchestrated via an Nginx API Gateway.

🚀 Key Architecture

The project is split into four decoupled services that communicate asynchronously using RabbitMQ and Celery:

🔐 Identity Service: Manages user authentication (JWT), role-based access control (Customer vs. Staff), and profile management.

💰 Account Service: Handles Savings & Current accounts services, balance management, loan management, tickets and secure PIN verification.

💸 Payment Service: Orchestrates internal transfers and card payments using atomic transactions and service-to-service API calls.

📖 Ledger Service: A passive consumer service that maintains an immutable double-entry ledger for all financial events to ensure data integrity.

🛠️ Tech Stack

Framework: Python, Django, Django Rest Framework (DRF)

Async Messaging: Celery, RabbitMQ (Topic Exchange routing)

Gateway: Nginx (Reverse Proxy)

Security: JWT (Shared Secret for inter-service auth), Custom Permissions

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
  pip install -r Requirements.txt
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

