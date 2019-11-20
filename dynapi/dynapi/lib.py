import json
import logging
import base64
import binascii
from pathlib import Path
import typing
import requests


logger = logging.getLogger(__name__)


def get_datasets_from_fs(path: str) -> typing.Generator[str, None, None]:
    """ Reads and decodes datasets in ```path``` """
    p = Path(path)
    for schema_path in p.glob("**/*.schema.json"):
        try:
            schema_file = open(schema_path)
            yield json.load(schema_file)
        except (IOError, json.JSONDecodeError):
            logger.error(
                f"File {schema_path} has invalid schema or resource", exc_info=True
            )


def get_datasets(schema_repo_url: str) -> typing.Generator[str, None, None]:
    """ Reads and decodes datasets from git repo """

    try:
        repo_url = f"{schema_repo_url}/contents"
        response = requests.get(repo_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception(f"Error getting schemas from {schema_repo_url}")
    else:
        for schema in response.json():
            try:
                schema_path = f"{repo_url}/{schema['path']}"
                response = requests.get(schema_path)
                response.raise_for_status()
                yield json.loads(base64.b64decode(response.json()["content"]))
            except requests.exceptions.HTTPError:
                logger.exception(
                    f"Schema at {schema_path} has invalid schema or resource"
                )
            except binascii.Error:
                logger.exception(f"Invalid b64 encoding in {schema_path}")
