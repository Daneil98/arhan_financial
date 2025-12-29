# payments/Dockerfile
# Fix for Render Build System
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
RUN chmod +x /app/start.sh

# ✅ Tell Docker the file is inside the subfolder
COPY frontend_service/Requirement.txt /webportal/
RUN pip install --no-cache-dir -r /webportal/Requirement.txt

COPY . frontend_service/ /webportal/

EXPOSE 8005

CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]