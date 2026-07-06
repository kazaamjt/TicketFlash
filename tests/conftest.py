# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
"""
Pytest fixtures live in thise file
"""
import os
import random
import string
from copy import deepcopy
from typing import Iterable

import pytest


@pytest.fixture
def tmp_env() -> Iterable[os._Environ[str]]:
    """
    Creates a temporary copy of os.environ
    and cleans it up after use.
    """
    env = deepcopy(os.environ)
    yield os.environ
    os.environ = env


@pytest.fixture
def random_string() -> str:
    return "".join(random.choice(string.printable) for _ in range(20))
