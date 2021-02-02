import unittest

from opslib.osm.validator import (
    ModelValidator,
    ValidationError,
    AttributeErrorTypes,
    validator,
)
from typing import Optional, List, Dict, Tuple, Set


MANDATORY_ATTRS = [
    "boolean",
    "integer",
    "string",
    "tuple_attr",
    "set_attr",
    "list_int",
    "list_str",
    "dict_str_int",
    "dict_int_str",
]

VALUES = {
    "boolean": False,
    "integer": 2,
    "string": "1",
    "tuple_attr": (1, 2),
    "set_attr": {1, 2},
    "list_int": [1, 2],
    "list_str": ["1", "2"],
    "dict_str_int": {"1": 1, "2": 2},
    "dict_int_str": {1: "1", 2: "2"},
}


class ExampleModel(ModelValidator):
    boolean: bool
    integer: int
    string: str
    tuple_attr: Tuple[int]
    set_attr: Set[int]
    list_int: List[int]
    list_str: List[str]
    dict_str_int: Dict[str, int]
    dict_int_str: Dict[int, str]
    opt_boolean: Optional[bool]
    opt_integer: Optional[int]
    opt_string: Optional[str]
    opt_tuple_attr: Optional[Tuple[int]]
    opt_set_attr: Optional[Set[int]]
    opt_list_int: Optional[List[int]]
    opt_list_str: Optional[List[str]]
    opt_dict_str_int: Optional[Dict[str, int]]
    opt_dict_int_str: Optional[Dict[int, str]]


class ExampleCustomValidationModel(ModelValidator):
    log_level: str

    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in {"INFO", "DEBUG"}:
            raise ValueError("value must be INFO or DEBUG")
        return v


class ExampleMissingOptionalAttribute(ModelValidator):
    optional: Optional[str]


class TestValidator(unittest.TestCase):
    def test_validator_all_success(self):
        data = {attr: VALUES[attr] for attr in MANDATORY_ATTRS}
        data.update({f"opt_{attr}": VALUES[attr] for attr in MANDATORY_ATTRS})
        model = ExampleModel(**data)
        for attr, value in data.items():
            self.assertEqual(model.__getattribute__(attr), value)

    def test_validator_mandatory_success(self):
        data = {attr: VALUES[attr] for attr in MANDATORY_ATTRS}
        model = ExampleModel(**data)
        for attr, value in data.items():
            self.assertEqual(model.__getattribute__(attr), value)

    def test_validator_mandatory_with_dash_success(self):
        data = VALUES
        model = ExampleModel(**data)
        for attr, value in data.items():
            self.assertEqual(model.__getattribute__(attr.replace("-", "_")), value)

    def test_validator_wrong(self):
        testing_data = {attr: None for attr in MANDATORY_ATTRS}
        testing_data.update({f"opt_{attr}": None for attr in MANDATORY_ATTRS})
        for testing_key in testing_data:
            testing_data[testing_key] = [
                wrong_value
                for key, wrong_value in VALUES.items()
                if key != testing_key and f"opt_{key}" != testing_key
            ]

        for i in range(len(VALUES) - 1):
            data = {k: v.pop() for k, v in testing_data.items()}
            raised = False
            try:
                ExampleModel(**data)
            except ValidationError as e:
                raised = True
                self.assertTrue(
                    all(
                        key in e.attribute_errors
                        and e.attribute_errors[key] == AttributeErrorTypes.INVALID_TYPE
                        for key in data
                        if not ("integer" in key and isinstance(data[key], bool))
                    )
                )
            self.assertTrue(raised)

    def test_validator_missing(self):
        data = {}
        raised = False
        try:
            ExampleModel(**data)
        except ValidationError as e:
            raised = True
            self.assertTrue(
                all(
                    key in e.attribute_errors
                    and e.attribute_errors[key] == AttributeErrorTypes.MISSING
                    for key in data
                )
            )
        self.assertTrue(raised)

    def test_custom_validator_success(self):
        data = {"log_level": "INFO"}
        ExampleCustomValidationModel(**data)

    def test_custom_validator_exception(self):
        raised = False
        wrong_data = {"log_level": "WRONG"}
        expected_error = "value must be INFO or DEBUG"
        try:
            ExampleCustomValidationModel(**wrong_data)
        except ValidationError as e:
            raised = True
            self.assertEqual(expected_error, e.attribute_errors["log_level"])
        self.assertTrue(raised)

    def test_missing_optional_attr(self):
        ExampleMissingOptionalAttribute(**{})