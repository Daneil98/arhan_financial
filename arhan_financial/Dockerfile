FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /Identity_service

# 1. Copy requirements from the CURRENT folder (payments/)
# Since we will set the context to 'payments', we don't need the folder prefix.
COPY Requirement.txt /Identity_service/

RUN pip install --no-cache-dir -r Requirement.txt

# 2. Copy the rest of the payments folder contents
COPY . /Identity_service/

# 3. Make sure the start script is executable
RUN chmod +x /Identity_service/start.sh

# 4. Run your start script
CMD ["./start.sh"]