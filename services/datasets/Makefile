test:
	pytest tests

start:
	FLASK_APP=app:app flask run --reload

graph:
	python graph.py | dot -Tpng > graph.png || echo "OK although segfault :D"