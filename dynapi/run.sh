export FLASK_APP=dynapi/app.py 
export FLASK_ENV=development 
export ROUTES_ROOT_DIR=./data 
export URI_PATH_PREFIX=/api/
export DATABASE_URL=postgres://postgres:@localhost:5434/postgres
flask run -p 5001
# bin/python dynapi/wsgi.py
