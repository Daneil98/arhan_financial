# arhan_financial/Dockerfile
# Fix for Render Build System
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN chmod +x /app/start.sh
# ✅ Tell Docker the file is inside the subfolder
COPY arhan_financial/Requirement.txt /Identity_service/
RUN pip install --no-cache-dir -r /Identity_service/Requirement.txt


COPY . arhan_financial/ /Identity_service/

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]