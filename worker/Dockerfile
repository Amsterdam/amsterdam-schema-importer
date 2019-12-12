FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

EXPOSE 8080

WORKDIR /app
COPY . /app
RUN pip install wheels/*
RUN pip install gunicorn
RUN pip install -e .

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["make", "run"]
