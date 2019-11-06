from dataservices import amsterdam_schema as aschema


class Type(aschema.Dataset):
    ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
    URI_VERSION_PREFIX = "latest"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {cls["id"]: self.primary_name(cls) for cls in self.classes}

    def primary_name(self, cls):
        id_fields = [
            k
            for k, v in cls["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == self.ID_REF
        ]
        return id_fields and id_fields[0] or None
