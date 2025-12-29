# ledger_service/Dockerfile
# Fix for Render Build System
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN chmod +x /app/start.sh
# ✅ Tell Docker the file is inside the subfolder
COPY ledger_service/Requirement.txt /ledger/
RUN pip install --no-cache-dir -r /ledger/Requirement.txt

COPY . ledger_service/ /ledger/

EXPOSE 8003

CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"]