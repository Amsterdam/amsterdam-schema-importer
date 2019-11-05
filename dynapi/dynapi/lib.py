import json
import logging
from pathlib import Path
import typing


logger = logging.getLogger(__name__)


def get_datasets(path: str) -> typing.Generator[str, None, None]:
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