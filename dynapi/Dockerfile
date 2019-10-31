FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

EXPOSE 6543

COPY ./requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install dataservices==0.0.3

WORKDIR /dynapi

# ENTRYPOINT ["/app/docker-entrypoint.sh"]
# CMD ["make", "run"]
