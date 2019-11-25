from flask import Blueprint
from flask import jsonify


status = Blueprint("status", __name__)


@status.route("/health")
def health():
    return jsonify({"status": "OK"})
