FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /account_service


COPY Requirement.txt /account_service/

RUN pip install --no-cache-dir -r Requirement.txt

COPY . /account_service/

# Make script executable
RUN chmod +x /account_service/start.sh

CMD ["./start.sh"]