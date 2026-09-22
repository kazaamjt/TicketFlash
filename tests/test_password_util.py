# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument

from ticket_flash.backend import password_util


def test_rotate(tmp_config_dir: None) -> None:
    assert not password_util.PEPPERS_FILE.exists()
    password_util.rotate_pepper()
    assert password_util.PEPPERS_FILE.exists()
    assert password_util.PEPPER_STRUCT.current_index == 0
    assert len(password_util.PEPPER_STRUCT.peppers) == 1

    password = "test"
    hashed_pass = password_util.hash_password(password)
    assert password_util.verify(password, 0, hashed_pass)

    password_util.rotate_pepper()
    assert password_util.PEPPER_STRUCT.current_index == 1
    assert len(password_util.PEPPER_STRUCT.peppers) == 2

    new_hashed_pass = password_util.hash_password(password)
    assert hashed_pass != new_hashed_pass
    assert password_util.verify(password, 0, hashed_pass)
    assert password_util.verify(password, 1, new_hashed_pass)
