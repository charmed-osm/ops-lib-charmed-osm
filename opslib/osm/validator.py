from collections.abc import Iterable
from typing import Any, List, Union

from typing_inspect import get_args, get_origin

__all__ = ["ValidationError", "ModelValidator", "AttributeErrorTypes", "validator"]


def validator(argument):
    def call(function):
        def wrapper(argument):
            result = function(ModelValidator, argument)
            return result

        wrapper.decorator = True
        wrapper.argument = argument
        return wrapper

    return call


class AttributeErrorTypes:
    INVALID_TYPE = "Invalid type"
    MISSING = "Missing attribute"
    UNDEFINED = "Undefined attribute"


class AttributeError(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

    def __str__(self):
        return f"{self.name}\n    {self.message}\n"


class ValidationError(Exception):
    _message = "{} validation errors.\n{}"

    def __init__(self, exceptions: List[AttributeError]):
        self.exceptions = exceptions
        self.attribute_errors = {e.name: e.message for e in self.exceptions}

    def __repr__(self):
        return self._message.format(
            len(self.exceptions),
            "".join([str(exception) for exception in self.exceptions]),
        )

    def __str__(self):
        return self.__repr__()

    def message(self):
        return "Errors found in: {}".format(", ".join([self.attribute_errors.keys()]))


class ModelValidator:
    def __init__(self, **data: Any):
        data = {k.replace("-", "_"): v for k, v in data.items()}

        values, validation_error = validate_model(self.__class__, data)

        if validation_error:
            raise validation_error

        setattr(self, "__dict__", values)


def validate_model(model, data):
    validation_exceptions = []
    model_attributes = getattr(model, "__annotations__")
    __decorator_validators__ = {
        validator.argument: validator
        for validator in model.__dict__.values()
        if hasattr(validator, "decorator")
    }
    error = None
    values = {}
    # extra_attributes = [key for key in data if key not in model_attributes]
    # if extra_attributes:
    #     for extra_attr in extra_attributes:
    #         validation_exceptions.append(
    #             AttributeError(extra_attr, AttributeErrorTypes.UNDEFINED)
    #         )

    for attr_name, attr_type in model_attributes.items():
        optional = _is_optional_type(attr_type)
        type_to_check = _safe_get_type(attr_type)
        args_type = _safe_get_args(attr_type)

        data_value = data.get(attr_name)
        if data_value is None and not optional:
            validation_exceptions.append(
                AttributeError(attr_name, AttributeErrorTypes.MISSING)
            )
        else:
            error_msg = ""
            try:
                _validate(data_value, type_to_check, args_type)
                if attr_name in __decorator_validators__:
                    data[attr_name] = __decorator_validators__[attr_name](data_value)
            except Exception as e:
                error_msg = str(e)
                validation_exceptions.append(AttributeError(attr_name, error_msg))
                continue
    if validation_exceptions:
        error = ValidationError(exceptions=validation_exceptions)
    else:
        values.update(
            {attr_name: data.get(attr_name) for attr_name in model_attributes}
        )

    return values, error


def _safe_get_type(obj_type):
    if _is_optional_type(obj_type):
        return _safe_get_type(obj_type.__args__[0])
    else:
        origin = get_origin(obj_type)
        return origin if origin is not None else obj_type


def _safe_get_args(obj_type):
    if _is_optional_type(obj_type):
        return _safe_get_args(obj_type.__args__[0])
    else:
        return get_args(obj_type)


def _is_optional_type(obj_type):
    origin = get_origin(obj_type)
    args = get_args(obj_type)
    return origin == Union and len(args) == 2 and args[1] is type(None)  # noqa: E721


def _validate(data_value, type_to_check, args_type):
    if data_value is not None:
        if not isinstance(data_value, type_to_check):
            raise Exception(AttributeErrorTypes.INVALID_TYPE)
        elif args_type and isinstance(data_value, Iterable):
            for v in data_value:
                tuple_of_types = (
                    (type(v), type(data_value[v]))
                    if isinstance(data_value, dict)
                    else (type(v),)
                )
                if tuple_of_types != args_type:
                    raise Exception(AttributeErrorTypes.INVALID_TYPE)
