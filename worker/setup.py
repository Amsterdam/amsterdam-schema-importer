from setuptools import setup
from setuptools import find_packages

setup(
    name="worker",
    version="0.0.1",
    description="Worker Flask app for dataservices",
    long_description="Worker Flask app for dataservices",
    author="Jan Murre",
    author_email="jan.murre@catalyz.nl",
    url="",
    packages=find_packages(),
    install_requires=[
        "Flask",
        "jsonref==0.2",
        "mappyfile",
        "dataservices>=0.0.3"
    ],
    extras_require={"tests": ["pytest"]},
)
