FROM nginx:stable-alpine
COPY default.conf /etc/nginx/conf.d
RUN apk add apache2-utils
EXPOSE 80/tcp
EXPOSE 443/tcp

RUN htpasswd -bc /etc/htpasswd_nginx \
    ${BRIEVENBUS_USER:-user} ${BRIEVENBUS_PASS:-insecure}

CMD ["/bin/sh", "-c", "exec nginx -g 'daemon off;';"]
WORKDIR /usr/share/nginx/html
