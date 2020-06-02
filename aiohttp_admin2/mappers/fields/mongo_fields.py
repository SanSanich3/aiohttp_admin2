from bson.objectid import ObjectId

from aiohttp_admin2.mappers.fields.abc import AbstractField


__all__ = ["ObjectIdField", ]


class ObjectIdField(AbstractField):

    def to_python(self) -> str:
        return str(self._value)

    def to_raw(self) -> ObjectId:
        if isinstance(self._value, str):
            return ObjectId(self._value)

        return self._value
