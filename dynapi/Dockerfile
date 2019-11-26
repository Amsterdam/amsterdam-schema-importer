FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

EXPOSE 8080

WORKDIR /app

COPY ./requirements.txt /app
COPY . /app

RUN pip install -r requirements.txt
RUN pip install dataservices==0.0.3

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
CMD ["make", "run"]

