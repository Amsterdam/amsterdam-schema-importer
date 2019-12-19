export FLASK_APP=worker/web.py 
export FLASK_ENV=development 
export SCHEMA_URL=https://schemas.data.amsterdam.nl/datasets/
flask run -p 5002 --host=0.0.0.0
# python -m pdb -m flask run -p 5002
