"""Helpers functions for dictionary."""

from typing import Any, Hashable, Optional


def get_key_by_value(dict_: dict, value: Any) -> Optional[Hashable]:
    gen_items = (item for item in dict_.items())
    result = list(filter(lambda item: item[1] == value, gen_items))
    return result[0][0] if result else None
