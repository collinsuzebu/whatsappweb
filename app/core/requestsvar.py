import contextvars
import types
import typing

global_request = contextvars.ContextVar("request_global",
                                        default=types.SimpleNamespace())

def gbl():
    return global_request.get()
