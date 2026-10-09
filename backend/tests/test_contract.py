"""Ответы backend соответствуют контракту (Schemathesis по `api/openapi.yaml`)."""

from typing import Any

import schemathesis
from schemathesis import Case

from app.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.include(path="/health").parametrize()
def test_health_matches_contract(case: Case[Any]) -> None:
    case.call_and_validate()
