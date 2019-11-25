run: export URI_PATH=/api/
run: 
	gunicorn dynapi.wsgi:application -w 1 -b 0.0.0.0:8080
