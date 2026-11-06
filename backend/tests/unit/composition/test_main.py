import sys

import pytest
from fastapi.testclient import TestClient

from app.adapter.decision.lexical import LexicalDecisionModel
from app.adapter.decision.system_one import SystemOneModel
from app.adapter.llm.claude_agent import ClaudeAgentModel
from app.adapter.llm.codex_agent import CodexAgentModel
from app.main import Providers, build_decision_model, build_language_model, create_app
from app.settings import ConfigError, DecisionProvider, LanguageProvider, Settings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("settings", "decision", "language"),
    [
        (Settings(), LexicalDecisionModel, type(None)),
        (
            Settings(
                decision_provider=DecisionProvider.SYSTEM_ONE,
                language_provider=LanguageProvider.CLAUDE,
            ),
            SystemOneModel,
            ClaudeAgentModel,
        ),
        (Settings(language_provider=LanguageProvider.CODEX), LexicalDecisionModel, CodexAgentModel),
    ],
)
async def test_settings_select_implementations(
    settings: Settings, decision: type, language: type
) -> None:
    decision_model = build_decision_model(settings)

    assert isinstance(decision_model, decision)
    assert isinstance(build_language_model(settings), language)
    await decision_model.aclose()


def test_lifespan_exposes_and_closes_providers() -> None:
    app = create_app(Settings(decision_provider=DecisionProvider.SYSTEM_ONE))

    with TestClient(app):
        providers = app.state.providers
        assert isinstance(providers, Providers)
        assert isinstance(providers.decision, SystemOneModel)
        assert not providers.decision._client.is_closed

    assert providers.decision._client.is_closed


def test_invalid_environment_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DECISION_MODEL", "jev")

    with pytest.raises(ConfigError, match="DECISION_MODEL"):
        create_app()


@pytest.mark.parametrize("provider", [LanguageProvider.CLAUDE, LanguageProvider.CODEX])
def test_missing_llm_group_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch, provider: LanguageProvider
) -> None:
    for module in ("claude_agent_sdk", "openai_codex"):
        monkeypatch.setitem(sys.modules, module, None)
    for module in ("app.adapter.llm.claude_agent", "app.adapter.llm.codex_agent"):
        monkeypatch.delitem(sys.modules, module, raising=False)

    with pytest.raises(ConfigError, match=f"LANGUAGE_MODEL={provider.value} needs package"):
        create_app(Settings(language_provider=provider))
