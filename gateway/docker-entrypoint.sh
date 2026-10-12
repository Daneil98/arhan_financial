#!/bin/sh
set -e

# Defaults target local docker-compose service names.
# On Railway, override these with private domains, e.g.:
#   IDENTITY_UPSTREAM=http://identity-service.railway.internal:8001
: "${PORT:=80}"
: "${IDENTITY_UPSTREAM:=http://identity:8001}"
: "${ACCOUNT_UPSTREAM:=http://account:8002}"
: "${PAYMENTS_UPSTREAM:=http://payments:8004}"
: "${LEDGER_UPSTREAM:=http://ledger:8003}"
: "${FRONTEND_UPSTREAM:=http://frontend:8005}"
: "${FRAUD_UPSTREAM:=http://fraud:8006}"

export PORT IDENTITY_UPSTREAM ACCOUNT_UPSTREAM PAYMENTS_UPSTREAM LEDGER_UPSTREAM FRONTEND_UPSTREAM FRAUD_UPSTREAM

envsubst '$PORT $IDENTITY_UPSTREAM $ACCOUNT_UPSTREAM $PAYMENTS_UPSTREAM $LEDGER_UPSTREAM $FRONTEND_UPSTREAM $FRAUD_UPSTREAM' \
  < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf

echo "Gateway listening on :$PORT"
echo "Upstreams: identity=$IDENTITY_UPSTREAM account=$ACCOUNT_UPSTREAM payments=$PAYMENTS_UPSTREAM ledger=$LEDGER_UPSTREAM frontend=$FRONTEND_UPSTREAM fraud=$FRAUD_UPSTREAM"

exec nginx -g 'daemon off;'
