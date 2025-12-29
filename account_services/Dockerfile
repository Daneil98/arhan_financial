# account_services/Dockerfile
# Fix for Render Build System
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
RUN chmod +x /app/start.sh
# ✅ Tell Docker the file is inside the subfolder
COPY account_services/Requirement.txt /account_service/
RUN pip install --no-cache-dir -r /account_service/Requirement.txt

COPY . account_services/ /account_service/

EXPOSE 8002

CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]