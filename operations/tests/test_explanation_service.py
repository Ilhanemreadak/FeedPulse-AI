import pytest

from operations.services import explanation_service
from operations.services.explanation_service import (
    _detect_provider,
    _rule_based_answer,
    _rule_based_explanation,
    answer_question,
    generate_explanation,
)

_PROVIDER_KEYS = [
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'DEEPSEEK_API_KEY',
    'GROQ_API_KEY',
    'GEMINI_API_KEY',
]


@pytest.fixture
def no_provider_env(monkeypatch):
    for key in _PROVIDER_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_detect_provider_none_when_no_keys(no_provider_env):
    assert _detect_provider() == (None, None)


def test_detect_provider_precedence(no_provider_env, monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'g')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'a')
    # OpenAI absent -> anthropic wins over groq by ordering
    assert _detect_provider() == ('anthropic', 'a')


def test_rule_based_explanation_escalates_priority():
    high = _rule_based_explanation({'temperature': 95})
    assert high['priority'] == 'high'
    assert high['provider'] == 'rule-based'

    medium = _rule_based_explanation({'energy_consumption': 70})
    assert medium['priority'] == 'medium'


def test_rule_based_explanation_no_findings():
    result = _rule_based_explanation({'temperature': 60, 'production_quality_score': 95})
    assert 'belirgin bir kural' in result['diagnosis']


def test_rule_based_answer_routes_by_keyword():
    data = {'temperature': 95, 'risk_level': 'high', 'anomaly_score': -0.05}
    assert 'Sıcaklık' in _rule_based_answer(data, 'Sıcaklık nedir?')
    assert 'Risk' in _rule_based_answer(data, 'risk seviyesi ne?')


def test_generate_explanation_falls_back_without_keys(no_provider_env):
    result = generate_explanation({'temperature': 95})
    assert result['provider'] == 'rule-based'


def test_generate_explanation_uses_llm_when_available(no_provider_env, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'k')
    monkeypatch.setattr(explanation_service, '_call_llm', lambda d, p, k: 'LLM yanıtı')
    result = generate_explanation({'temperature': 95})
    assert result['provider'] == 'openai'
    assert result['recommendation'] == 'LLM yanıtı'


def test_answer_question_falls_back_without_keys(no_provider_env):
    answer = answer_question({'temperature': 95}, 'Sıcaklık nedir?')
    assert 'Sıcaklık' in answer
