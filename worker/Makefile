run:
	uwsgi --socket 0.0.0.0:8080 --protocol=http -w worker.web:app

docs:
	(cd ../; pdoc3 --http localhost:5000 worker)
