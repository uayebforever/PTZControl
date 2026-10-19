import random
import string
from enum import Enum
from typing import TypeVar, Type, Callable, Sequence

_T = TypeVar("_T")
_T_Enum = TypeVar("_T_Enum", bound=Enum)


def random_string(length: int = 8) -> str:
    return "".join(random.sample(string.ascii_letters, length))


def random_int(max: int =100000000) -> int:
    return random.randint(0, max)

def random_enum(enum: Type[_T_Enum]) -> _T_Enum:
    return random.choice(list(enum))


def random_excluding(random_provider: Callable[[], _T], excluding: Sequence[_T]) -> _T:
    attempts = 1
    value = random_provider()
    while value in excluding and attempts < 1000:
        value = random_provider()
    if value in excluding:
        raise RuntimeError("random_excluding: unable to find satisfactory random value")
    return value
