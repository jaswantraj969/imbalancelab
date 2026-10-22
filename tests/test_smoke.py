"""Smoke tests: the package and all subpackages import, and defaults are as specified."""

import importlib

import pytest

SUBPACKAGES = [
    "data",
    "profiling",
    "splitting",
    "pipelines",
    "models",
    "evaluation",
    "tracking",
    "reporting",
    "api",
]


def test_package_exposes_version() -> None:
    import imbalancelab

    assert imbalancelab.__version__ == "0.1.0"


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports(name: str) -> None:
    module = importlib.import_module(f"imbalancelab.{name}")
    assert module.__doc__


def test_config_default_seed_is_42() -> None:
    from imbalancelab.config import Settings

    # _env_file=None ignores any local .env so the test checks the coded default.
    assert Settings(_env_file=None).seed == 42
