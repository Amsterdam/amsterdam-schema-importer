from dataclasses import dataclass, asdict
import functools
import typing

from flask import Flask, request
_api = Flask("import")

from . import types


class RequestContext:
    pass


@dataclass
class Request:
    params: dict

    @property
    def json(self):
        return request.json


class EventRequest(Request):
    """ Request is coupled with an domain event """

    event_cls: types.Event

    @property
    def obj(self):
        """ Instantiate an event with request data """
        return self.event_cls(**self.json)


class API:
    def __init__(self,
                 name: str,
                 backend_cls=Flask, context_cls=RequestContext,
                 request_cls=Request):
        self.backend = backend_cls(name)
        self.context_cls = context_cls
        self.request_cls = request_cls
    
    def route(self, path, methods: typing.List[str]):
        def wrapper(func: typing.Callable):
            request_cls = func.__annotations__['request']
            @functools.wraps(func)
            def wrapped(**kwargs):
                result = func(
                    self.context_cls(),
                    request_cls(params=kwargs),
                )
                if isinstance(result, types.Event):
                    return asdict(result)
                return result
            return self.backend.route(
                path, methods=methods
            )(wrapped)
        return wrapper