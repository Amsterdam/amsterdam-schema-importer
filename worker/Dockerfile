FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

EXPOSE 8766

COPY ./requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["make", "run"]