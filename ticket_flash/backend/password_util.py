"""
All the logic, to create, hash, salt, pepper and verify passwords.
"""

import base64
import hashlib
import hmac
import json
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel

from .. import config
from ..types import assert_type

_ARGON_MEM_COST = config.get_int("sec", "argon_memory_cost", 19456)
_ARGON_TIME_COST = config.get_int("sec", "argon_time_cost", 2)
_ARGON_PARALLELISM = config.get_int("sec", "argon_parallelism", 1)

# Configure Argon2id.
_ARGON_HASHER = PasswordHasher(
    memory_cost=_ARGON_MEM_COST,
    time_cost=_ARGON_TIME_COST,
    parallelism=_ARGON_PARALLELISM,
)


class PepperStruct(BaseModel):
    """Keeps track of our peppers once loaded."""

    current_index: int
    peppers: dict[int, str]
    loaded: bool = False

    def get_current_pepper(self) -> str:
        return self.peppers[self.current_index]


PEPPER_STRUCT = PepperStruct(current_index=0, peppers={})


def _pepper(pepper: str, string: str) -> str:
    digest = hmac.new(
        pepper.encode("utf-8"),
        string.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("ascii")


def hash_password(string: str) -> str:
    return _ARGON_HASHER.hash(_pepper(PEPPER_STRUCT.get_current_pepper(), string))


def verify(string: str, pepper_index: int, stored_hash: str) -> bool:
    """Verify a string matches the hashed version passed"""
    try:
        return _ARGON_HASHER.verify(
            stored_hash,
            _pepper(PEPPER_STRUCT.peppers[pepper_index], string),
        )
    except VerifyMismatchError:
        return False


def gen_pepper() -> str:
    """Generate a new, secure pepper."""
    return secrets.token_bytes(32).hex()


def print_pepper(pepper: str) -> None:
    """Prints a pepper nicely to the screen."""
    output = f"pepper: {pepper}"
    print("\n" + "=" * len(output))
    print(output)
    print("=" * len(output) + "\n")


PEPPERS_FILE = config.get_config_dir() / ".tf_peppers"


def _load_peppers() -> PepperStruct:
    global PEPPER_STRUCT  # pylint: disable=global-statement
    if PEPPERS_FILE.exists() and not PEPPER_STRUCT.loaded:
        with PEPPERS_FILE.open(encoding="utf-8") as f:
            PEPPER_STRUCT = PepperStruct(**assert_type(json.load(f), dict), loaded=True)

    return PEPPER_STRUCT


def _save_peppers(pepper_struct: PepperStruct) -> None:
    with PEPPERS_FILE.open(mode="w") as f:
        f.write(pepper_struct.model_dump_json(indent=4, exclude={"loaded"}))


def rotate_pepper() -> PepperStruct:
    """
    This will generate a new pepper and update the pepper file.
    Optionally removes the old peppers.

    Returns a dict with all the peppers and the current pepper seperately.
    """
    pepper_struct = _load_peppers()
    if len(pepper_struct.peppers) == 0:
        new_index = 0
    else:
        new_index = pepper_struct.current_index + 1
    new_pepper = gen_pepper()
    pepper_struct.peppers[new_index] = new_pepper
    pepper_struct.current_index = new_index

    _save_peppers(pepper_struct)
    return pepper_struct


def clean() -> None:
    """Cleans up old peppers that are no longer in use."""
    peppers = _load_peppers()
    # DO THE CLEANUP
    _save_peppers(peppers)
