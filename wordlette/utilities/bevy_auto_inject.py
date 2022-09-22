import inspect

from bevy import Bevy, bevy_method, Inject


class BevyAutoInject(Bevy):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for name, member in vars(cls).items():
            if (wrapped := inspect.unwrap(member)) != member:
                member = wrapped

            if inspect.isfunction(member) and requires_injection(member):
                method = bevy_method(member)
                setattr(cls, name, method)


def requires_injection(method) -> bool:
    sig = inspect.signature(method)
    for param in sig.parameters.values():
        if isinstance(param.default, Inject):
            return True

        if isinstance(param.default, type) and issubclass(param.default, Inject):
            return True

    return False
