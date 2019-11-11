# XXX Here we need to provide the more specific error handling
# as required in NL API and defined in RFC 7807


class InvalidInputException(Exception):
    pass


class NotFoundException(Exception):
    pass
