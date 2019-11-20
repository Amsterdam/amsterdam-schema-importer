export FLASK_APP=dynapi/app.py 
export FLASK_ENV=development 
export ROUTES_ROOT_DIR=./data 
export SCHEMA_REPO_URL=https://api.github.com/repos/jjmurre/schematest
export URI_PATH=/
export DATABASE_URL=postgres://postgres:@localhost:5434/postgres
bin/flask run -p 5001
# bin/python dynapi/wsgi.py
