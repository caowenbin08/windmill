import logging
import re
from unittest import TestCase

from airflow.operators.bash_operator import BaseOperator, BashOperator
from airflow.operators.python_operator import PythonVirtualenvOperator
from airflow.operators.sensors import S3KeySensor

from windmill.models.schemas.app_schemas import OperatorSchema
from windmill.models.operators.operator_handler import OperatorHandler
from windmill.models.operators.operator_index import OperatorIndex
from windmill.utils.class_parser import ClassParser


def test_fix_docstring():
    assert """Some description...

:param str param1: some param
:type param1: str
""" == ClassParser.fix_docstring(
        """Some description...

:param param1: some param
:type param1: str
"""
    )


class TestOperatorMarshalling(TestCase):
    test_input = {
        "type": "bool-param",
        "properties": {
            "parameters": [
                {
                    "id": "useLegacySql",
                    "type": "bool",
                    "default": "true",
                    "required": False,
                }
            ]
        },
    }

    def test_dict_to_operator(self):
        operator_data = OperatorSchema().load(self.test_input)
        self.assertDictEqual(operator_data, self.test_input)

    def test_marshall_result_to_operator_handler(self):
        operator_data = OperatorSchema().load(self.test_input)
        oh = OperatorHandler.from_marsh(operator_data)
        assert oh

        marshalled_oh = oh.dump()

        self.assertDictEqual(marshalled_oh, operator_data)

    def test_operator_to_operator_handler(self):
        oh = OperatorHandler.from_operator(BashOperator)
        bash_data = oh.dump()

        assert bash_data["type"] == "BashOperator"
        assert bash_data["properties"]["module"] == "airflow.operators.bash_operator"
        self.assertListEqual(
            [
                p["id"]
                for p in bash_data["properties"]["parameters"]
                if not p.get("inheritedFrom", False)
            ],
            ["bash_command", "xcom_push", "env", "output_encoding"],
        )

        # Bash Command is described - check length to minimise fragility
        assert bash_data["properties"]["parameters"][0]["description"]
        assert len(bash_data["properties"]["parameters"][0]["description"]) > 10
        assert bash_data["properties"]["parameters"][0]["type"] == "str"


class TestOperatorIndex(TestCase):
    def test_get_default_operators(self):
        ops = OperatorIndex.get_default_operators()
        assert ops
        assert all([issubclass(o, BaseOperator) for o in ops])

    def test_operator_list_marshalling(self):
        oi = OperatorIndex()
        operator_list = oi.marshall_operator_list()
        assert operator_list
        for op in operator_list:
            assert op["type"]
            for param_dict in op["properties"]["parameters"]:
                try:
                    assert re.match(r"[a-zA-Z_]+", param_dict["id"])
                except AssertionError as e:
                    logging.info(op)
                    raise e
