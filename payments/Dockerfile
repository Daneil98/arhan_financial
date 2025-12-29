# payments/Dockerfile
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN chmod +x /app/start.sh
# ✅ Tell Docker the file is inside the subfolder
COPY Requirement.txt /app/
RUN pip install --no-cache-dir -r Requirement.txt

COPY . /app/

EXPOSE 8004

CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]