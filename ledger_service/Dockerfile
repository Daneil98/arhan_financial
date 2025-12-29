FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /ledger

# ✅ CORRECT: Just copy the file name. 
# Since we are inside 'account_services/', the file is right here.
COPY Requirment.txt /ledger/

RUN pip install --no-cache-dir -r Requirment.txt

# ✅ CORRECT: Copy everything from the current folder (account_services)
COPY . /ledger/

# Make script executable
RUN chmod +x /ledger/start.sh

CMD ["./start.sh"]
