test:
	pytest tests

start:
	FLASK_APP=datasets.app:app flask run --reload

graph:
	python3.8 graph.py | dot -Tpng > graph.png || echo "OK although segfault :D"
