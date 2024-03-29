# pylint: disable=E0213
import re
from typing import Optional


from ..validator import ModelValidator, validator


class MysqlModel(ModelValidator):
    mysql_uri: Optional[str]
    _compiled_regex = re.compile(
        r"^mysql\:\/\/{}@{}\/{}?$".format(
            r"(?P<username>[_\w]+):(?P<password>[\w\W]+)",
            r"(?P<host>[\.\w]+):(?P<port>\d+)",
            r"(?P<database>[_\w]+)",
        )
    )

    @classmethod
    def _extract_data_from_uri(cls, v):
        match = cls._compiled_regex.search(v)
        if match:
            return match.groupdict()
        else:
            raise ValueError("mysql_uri is not properly formed")

    @validator("mysql_uri")
    def validate_mysql_uri(cls, v):
        cls.mysql_data = MysqlModel._extract_data_from_uri(v) if v else {}
        return v

    @property
    def host(cls):
        return cls.mysql_data.get("host")

    @property
    def port(cls):
        return int(cls.mysql_data.get("port")) if cls.mysql_data else None

    @property
    def username(cls):
        return cls.mysql_data.get("username")

    @property
    def password(cls):
        return cls.mysql_data.get("password")

    @property
    def database(cls):
        return cls.mysql_data.get("database")
