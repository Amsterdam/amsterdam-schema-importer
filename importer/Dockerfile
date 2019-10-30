FROM node:12

EXPOSE 8080

WORKDIR /app

COPY . /app
RUN npm install
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["make", "run"]
