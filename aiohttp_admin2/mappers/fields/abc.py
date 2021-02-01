import typing as t
from abc import (
    ABC,
    abstractmethod,
)

from aiohttp_admin2.mappers.exceptions import ValidationError

__all__ = ['AbstractField', ]


# todo: add validators


class AbstractField(ABC):
    type_name: str = 'string'

    def __init__(
        self,
        *,
        required: bool = False,
        validators: t.List[t.Callable[[t.Any], bool]] = None,
        value: t.Optional[str] = None,
        default: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> None:
        self.default: t.Optional[str] = default
        self._value: t.Optional[str] = default if value is None else value
        self.errors: t.List[t.Optional[str]] = []
        self.required = required
        # todo: add validator
        self.validators = validators or []

    @abstractmethod
    def to_python(self) -> t.Any:
        """
        Convert value to correct python type equivalent.

        Raises:
            ValueError: if type of value is wrong
        """
        pass

    def to_storage(self) -> str:
        """
        Convert value to correct storage type.
        """
        return str(self._value) if self._value is not None else ''

    @property
    def value(self) -> t.Any:
        """
        Convert value to correct python type equivalent.

        Raises:
            ValueError: if type of value is wrong
        """
        return self.to_python()

    @property
    def raw_value(self) -> t.Any:
        return self.to_storage()

    def is_valid(self) -> bool:
        """
        In this method check is current field valid and have correct value.

        Raises:
            ValidationError: if failed validators
            ValueError, TypeError: if type of value is wrong

        """
        if self.required and not self._value:
            raise ValidationError("field is required.")

        self.to_python()
        self.to_storage()

        for validator in self.validators:
            validator(self.value)

        return True

    def __call__(self, value: t.Any) -> "AbstractField":
        return self.__class__(
            required=self.required,
            validators=self.validators,
            default=self.default,
            value=value
        )

    def __repr__(self):
        return \
            f"{self.__class__.__name__}(name={self.type_name}," \
            f" value={self._value}), required={self.required}"
