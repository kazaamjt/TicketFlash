# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
import os
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path

import pytest

from ticket_flash import config


def test_config(tmp_env: os._Environ[str]) -> None:
    tmp_env["TF_TEST_TEST_VAR_1"] = "this_is_a_test"
    tmp_env["TF_TEST_TEST_VAR_2"] = "2"
    tmp_env["TF_TEST_TEST_VAR_3"] = "yes"
    tmp_env["TF_TEST_TEST_VAR_4"] = "/root"

    assert config.get("test", "test-var-1") == "this_is_a_test"
    assert config.get_int("test", "test-var-2") == 2
    assert config.get_bool("test", "test-var-3") is True
    assert config.get_path("test", "test-var-4") == Path("/root")

    with pytest.raises(config.BadOptionValue):
        config.get_int("test", "test-var-1")

    with pytest.raises(config.BadOptionValue):
        config.get_bool("test", "test-var-1")

    tmp_env["TF_TEST_TEST_VAR_FALSE"] = "no"
    assert config.get_bool("test", "test-var-false") is False

    tmp_env["TF_TEST_TEST_VAR_TRUE"] = "on"
    tmp_env["TF_TEST_TEST_VAR_FALSE"] = "off"
    assert config.get_bool("test", "test-var-True") is True
    assert config.get_bool("test", "test-var-false") is False


def test_get_multi(tmp_env: os._Environ[str]) -> None:
    tmp_env["TF_TEST_MULTI_1"] = "this_is_a_test"
    option_1 = config.get_multichoice(
        "test", "multi-1", ["this_is_a_test", "this_is_another_test"]
    )
    assert option_1 == "this_is_a_test"

    tmp_env["TF_TEST_MULTI_2"] = "this_is_another_test"
    option_2 = config.get_multichoice(
        "test", "multi-2", ["this_is_a_test", "this_is_another_test"]
    )
    assert option_2 == "this_is_another_test"

    default = config.get_multichoice(
        "test", "multi-3", ["this_is_a_test", "this_is_another_test"], "not_in_the_test"
    )
    assert default == "not_in_the_test"


def test_get_ip(tmp_env: os._Environ[str]) -> None:
    tmp_env["TF_TEST_IP_1"] = "0.0.0.0"
    option_1 = config.get_ip("test", "ip_1", IPv4Address("127.0.0.1"), IPv4Address)
    assert option_1 == IPv4Address("0.0.0.0")

    option_2 = config.get_ip("test", "ip_2", IPv4Address("127.0.0.1"), IPv4Address)
    assert option_2 == IPv4Address("127.0.0.1")

    with pytest.raises(config.BadOptionValue):
        config.get_ip("test", "ip_2", IPv4Address("127.0.0.1"), IPv6Address)
