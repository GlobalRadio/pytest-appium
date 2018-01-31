import wrapt
import functools
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

DEFAULT_REGISTRATION_NAME = 'base'

MIXIN_CLASSS = defaultdict(list)


def register_proxy_mixin(cls=None, *, name=DEFAULT_REGISTRATION_NAME):
    if cls == None:
        return functools.partial(register_proxy_mixin, name=name)
    assert isinstance(cls, type), "Decorator is for use on class's only"
    MIXIN_CLASSS[name].append(cls)
    return cls


@functools.lru_cache()
def _generate_proxy_class(name=DEFAULT_REGISTRATION_NAME):
    return type(name, (wrapt.ObjectProxy,) + tuple(MIXIN_CLASSS[name]), {})


def proxy(obj, name=DEFAULT_REGISTRATION_NAME):
    obj_proxy = _generate_proxy_class(name)(obj)
    for mixin in MIXIN_CLASSS[name]:
        mixin.__init__(obj_proxy)
    return obj_proxy
