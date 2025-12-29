# payments/Dockerfile
# Fix for Render Build System
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN chmod +x /app/start.sh
# ✅ Tell Docker the file is inside the subfolder
COPY payments/requirements.txt /payment/
RUN pip install --no-cache-dir -r /payment/requirements.txt

# Copy the payment folder into /payment inside container
COPY payments/ /payment/

EXPOSE 8004

CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]