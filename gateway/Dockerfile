FROM nginx:stable-alpine

# envsubst for templating upstream URLs + $PORT at container start
RUN apk add --no-cache gettext

COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
