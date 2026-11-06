import pytest

from app.adapter.decision.system_one import TYPESAFE_URL
from app.settings import ConfigError, DecisionProvider, LanguageProvider, Settings, load_settings


def test_empty_environment_selects_offline_providers() -> None:
    assert load_settings({}) == Settings()
    assert Settings().decision_provider is DecisionProvider.LEXICAL
    assert Settings().language_provider is LanguageProvider.NONE


def test_environment_selects_paid_providers() -> None:
    settings = load_settings(
        {
            "DECISION_MODEL": "system_one",
            "DECISION_MODEL_URL": "http://laya:8000",
            "DECISION_MODEL_API_KEY": "secret",
            "DECISION_MODEL_TIMEOUT_S": "2.5",
            "LANGUAGE_MODEL": "codex",
        }
    )

    assert settings == Settings(
        decision_provider=DecisionProvider.SYSTEM_ONE,
        decision_url="http://laya:8000",
        decision_api_key="secret",
        decision_timeout_s=2.5,
        language_provider=LanguageProvider.CODEX,
    )


def test_blank_values_fall_back_to_defaults() -> None:
    settings = load_settings({"DECISION_MODEL_URL": "", "DECISION_MODEL_API_KEY": ""})

    assert settings.decision_url == TYPESAFE_URL
    assert settings.decision_api_key is None


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"DECISION_MODEL": "jev"}, "DECISION_MODEL='jev' is not supported; use one of: lexical"),
        ({"LANGUAGE_MODEL": "gpt"}, "LANGUAGE_MODEL='gpt' is not supported; use one of: none"),
        ({"DECISION_MODEL_TIMEOUT_S": "soon"}, "DECISION_MODEL_TIMEOUT_S='soon' is not a number"),
        ({"DECISION_MODEL_TIMEOUT_S": "0"}, "DECISION_MODEL_TIMEOUT_S='0' must be positive"),
    ],
)
def test_invalid_value_names_the_variable(env: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message.replace("(", r"\(")):
        load_settings(env)
