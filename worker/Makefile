run:
	uwsgi -w worker.web:app --enable-threads
	# gunicorn worker.web:app -w 1 -b 0.0.0.0:8080
	# bash worker/run.sh

docs:
	(cd ../; pdoc3 --http localhost:5000 worker)
