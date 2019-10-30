export FLASK_APP=dynapi/wsgi.py 
export FLASK_ENV=development 
export ROUTES_ROOT_DIR=./data 
export DATABASE_URL=postgres://postgres:@localhost:5434/postgres
bin/flask run -p 5001
