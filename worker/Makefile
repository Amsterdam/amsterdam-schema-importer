run:
	uwsgi -w worker.web:app

docs:
	(cd ../; pdoc3 --http localhost:5000 worker)
