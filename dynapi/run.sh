cd $(dirname $0)
export FLASK_APP=dynapi/wsgi.py 
export FLASK_ENV=development 
export ROUTES_ROOT_DIR=$(pwd)/../data 
export URI_PATH=/
export DATABASE_URL=postgres://postgres:@localhost:5434/postgres
# bin/flask run -p 5001
bin/python dynapi/wsgi.py
