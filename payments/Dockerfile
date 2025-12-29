FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /payment

# 1. Copy requirements from the CURRENT folder (payments/)
# Since we will set the context to 'payments', we don't need the folder prefix.
COPY Requirement.txt /payment/

RUN pip install --no-cache-dir -r Requirement.txt

# 2. Copy the rest of the payments folder contents
COPY . /payment/

# 3. Make sure the start script is executable
RUN chmod +x /payment/start.sh

# 4. Run your start script
CMD ["./start.sh"]