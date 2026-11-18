"""Tests for Gemini retry / model-fallback behaviour (no network)."""

from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors

from app.services import gemini_service as gs_module
from app.services.gemini_service import GeminiService, GeminiUnavailableError


def _api_error(code: int) -> genai_errors.APIError:
    return genai_errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


class FakeModels:
    def __init__(self, script):
        self.script = script  # model -> list of outcomes (Exception or text)
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        outcome = self.script[model].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(gs_module.time, "sleep", lambda s: None)
    monkeypatch.setattr(gs_module.settings, "GEMINI_MODEL", "primary")
    monkeypatch.setattr(gs_module.settings, "GEMINI_FALLBACK_MODELS", "backup")
    monkeypatch.setattr(gs_module.settings, "GEMINI_MAX_RETRIES", 1)


def _service(script):
    svc = GeminiService(api_key="test")
    svc.client = SimpleNamespace(models=FakeModels(script))
    return svc


def test_overloaded_primary_falls_back():
    svc = _service({"primary": [_api_error(503), _api_error(503)], "backup": ["hello"]})
    assert svc.generate_text("hi") == "hello"
    assert svc.client.models.calls == ["primary", "primary", "backup"]


def test_retired_model_skips_without_retry():
    svc = _service({"primary": [_api_error(404)], "backup": ["ok"]})
    assert svc.generate_text("hi") == "ok"
    assert svc.client.models.calls == ["primary", "backup"]


def test_transient_error_retried_on_same_model():
    svc = _service({"primary": [_api_error(429), "recovered"], "backup": []})
    assert svc.generate_text("hi") == "recovered"


def test_auth_error_is_not_masked():
    svc = _service({"primary": [_api_error(403)], "backup": ["never"]})
    with pytest.raises(genai_errors.APIError):
        svc.generate_text("hi")


def test_all_models_failing_raises_clear_error():
    svc = _service({"primary": [_api_error(503)] * 2, "backup": [_api_error(503)] * 2})
    with pytest.raises(GeminiUnavailableError, match="All Gemini models failed"):
        svc.generate_text("hi")


def test_missing_key_raises_instead_of_stub():
    svc = GeminiService(api_key="x")
    svc.client = None
    with pytest.raises(GeminiUnavailableError, match="GEMINI_API_KEY"):
        svc.generate_text("hi")
