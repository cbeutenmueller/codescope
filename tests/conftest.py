from __future__ import annotations
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def java_order_service() -> Path:
    return FIXTURES / "java" / "OrderService.java"


@pytest.fixture
def java_user_controller() -> Path:
    return FIXTURES / "java" / "UserController.java"


@pytest.fixture
def angular_items_component() -> Path:
    return FIXTURES / "angular" / "items.component.ts"


@pytest.fixture
def default_config():
    from codescope.config import AppConfig

    return AppConfig()
