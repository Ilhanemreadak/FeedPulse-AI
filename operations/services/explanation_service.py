import logging
import os

logger = logging.getLogger('feedpulse.llm')

SYSTEM_PROMPT = (
    "Sen üretim operasyonları için çalışan bir AI karar destek asistanısın. "
    "Aşağıdaki üretim kaydını teknik olmayan operasyon diliyle açıkla. "
    "Cevabın kısa, net ve aksiyon odaklı olsun. "
    "Riskin neden oluştuğunu, olası sebebi ve önerilen aksiyonu belirt."
)

QA_SYSTEM_PROMPT = (
    "Sen bir üretim operasyonları AI asistanısın. "
    "Sana bir üretim kaydının sensör verileri ve kullanıcının sorusu verilecek. "
    "Soruyu kısa, net ve Türkçe olarak cevapla. Teknik ama anlaşılır ol."
)

# Rule-based / Q&A thresholds (also used by the rule-based fallbacks).
TEMP_HIGH = 85  # °C
VIBRATION_HIGH = 7  # mm/s
ENERGY_HIGH = 65  # kWh
QUALITY_LOW = 85  # /100
HUMIDITY_HIGH = 70  # %
PRESSURE_HIGH = 5  # bar
VOLUME_LOW = 60  # unit


def _detect_provider():
    """Return (provider, api_key) for the first available key, or (None, None)."""
    checks = [
        ('openai', os.getenv('OPENAI_API_KEY')),
        ('anthropic', os.getenv('ANTHROPIC_API_KEY')),
        ('deepseek', os.getenv('DEEPSEEK_API_KEY')),
        ('groq', os.getenv('GROQ_API_KEY')),
        ('gemini', os.getenv('GEMINI_API_KEY')),
    ]
    for provider, key in checks:
        if key:
            return provider, key
    return None, None


def generate_explanation(data: dict) -> dict:
    provider, api_key = _detect_provider()
    if provider:
        try:
            logger.info("LLM explanation via %s", provider)
            return _llm_explanation(data, provider, api_key)
        except Exception as e:
            logger.exception("LLM explanation FAILED (%s): %s -> rule-based fallback", provider, e)
    else:
        logger.info("No LLM key found -> rule-based explanation")
    return _rule_based_explanation(data)


def _llm_explanation(data: dict, provider: str, api_key: str) -> dict:
    text = _call_llm(data, provider, api_key)
    return {
        'diagnosis': text[:200],
        'possible_reason': f'{provider.capitalize()} tarafından analiz edildi.',
        'recommendation': text,
        'priority': 'medium',
        'provider': provider,
    }


def _build_llm(provider: str, api_key: str, temperature: float = 0.3):
    """Return a configured LangChain chat model for the given provider."""
    if provider == 'openai':
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model='gpt-4o-mini', api_key=api_key, temperature=temperature)

    if provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model='claude-haiku-4-5-20251001', api_key=api_key, temperature=temperature
        )

    if provider == 'deepseek':
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model='deepseek-chat',
            api_key=api_key,
            base_url='https://api.deepseek.com',
            temperature=temperature,
        )

    if provider == 'groq':
        from langchain_groq import ChatGroq

        return ChatGroq(model='llama3-8b-8192', api_key=api_key, temperature=temperature)

    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model='gemini-1.5-flash', google_api_key=api_key, temperature=temperature
        )

    raise ValueError(f"Unknown provider: {provider}")


def _call_llm(data: dict, provider: str, api_key: str) -> str:
    llm = _build_llm(provider, api_key)
    return _langchain_invoke(llm, SYSTEM_PROMPT, f"Üretim verisi: {data}")


def _langchain_invoke(llm, system_content: str, human_content: str) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    response = llm.invoke(
        [
            SystemMessage(content=system_content),
            HumanMessage(content=human_content),
        ]
    )
    return response.content.strip()


def _rule_based_explanation(data: dict) -> dict:
    findings = []
    priority = 'low'

    temp = data.get('temperature')
    vibration = data.get('vibration_level')
    energy = data.get('energy_consumption')
    quality = data.get('production_quality_score')
    humidity = data.get('humidity')
    pressure = data.get('pressure')
    volume = data.get('production_volume')

    if temp and temp > TEMP_HIGH:
        findings.append("Sıcaklık normalin üzerinde.")
        priority = 'high'
    if vibration and vibration > VIBRATION_HIGH:
        findings.append("Titreşim seviyesi yüksek, makine zorlanması olabilir.")
        priority = 'high'
    if energy and energy > ENERGY_HIGH:
        findings.append("Enerji tüketimi üretim miktarına göre yüksek.")
        if priority == 'low':
            priority = 'medium'
    if quality and quality < QUALITY_LOW:
        findings.append("Kalite skoru düşük.")
        if priority == 'low':
            priority = 'medium'
    if humidity and humidity > HUMIDITY_HIGH:
        findings.append("Nem seviyesi yüksek, hammadde veya ortam koşulları etkilenmiş olabilir.")
        if priority == 'low':
            priority = 'medium'
    if pressure and pressure > PRESSURE_HIGH:
        findings.append("Basınç değeri normalin üzerinde.")
        if priority == 'low':
            priority = 'medium'
    if volume and volume < VOLUME_LOW:
        findings.append("Üretim hacmi beklenen seviyenin altında.")
        if priority == 'low':
            priority = 'medium'

    if not findings:
        diagnosis = "Anomali tespit edildi ancak belirgin bir kural tetiklenmedi."
        possible_reason = "Birden fazla parametrenin eşzamanlı sapması model tarafından anomali olarak değerlendirildi."
        recommendation = "Tüm sensör değerlerini gözden geçirin ve önceki kayıtlarla karşılaştırın."
    else:
        diagnosis = " ".join(findings)
        possible_reason = "Makine veya süreç parametrelerinde normal dışı değerler tespit edildi."
        recommendation = _get_recommendation(priority)

    return {
        'diagnosis': diagnosis,
        'possible_reason': possible_reason,
        'recommendation': recommendation,
        'priority': priority,
        'provider': 'rule-based',
    }


def answer_question(data: dict, question: str) -> str:
    """Answer a follow-up question about a specific production record."""
    provider, api_key = _detect_provider()
    if provider:
        try:
            logger.info("LLM answer via %s | q=%r", provider, question[:60])
            return _call_llm_question(data, question, provider, api_key)
        except Exception as e:
            logger.exception("LLM answer FAILED (%s): %s -> rule-based fallback", provider, e)
    else:
        logger.info("No LLM key found -> rule-based answer")
    return _rule_based_answer(data, question)


def _call_llm_question(data: dict, question: str, provider: str, api_key: str) -> str:
    llm = _build_llm(provider, api_key)
    human_content = f"Üretim kaydı:\n{data}\n\nKullanıcı sorusu: {question}"
    return _langchain_invoke(llm, QA_SYSTEM_PROMPT, human_content)


def _rule_based_answer(data: dict, question: str) -> str:
    q = question.lower()
    if any(w in q for w in ['sıcaklık', 'sicaklik', 'temperature', 'ısı']):
        val = data.get('temperature')
        return f"Sıcaklık değeri: {val}°C. {f'Normalin üzerinde (>{TEMP_HIGH}°C).' if val and val > TEMP_HIGH else 'Normal aralıkta.'}"
    if any(w in q for w in ['titreşim', 'titresim', 'vibration']):
        val = data.get('vibration_level')
        return f"Titreşim seviyesi: {val} mm/s. {f'Yüksek (>{VIBRATION_HIGH} mm/s), makine zorlanıyor olabilir.' if val and val > VIBRATION_HIGH else 'Normal aralıkta.'}"
    if any(w in q for w in ['enerji', 'energy', 'kwh']):
        val = data.get('energy_consumption')
        return f"Enerji tüketimi: {val} kWh. {f'Yüksek (>{ENERGY_HIGH} kWh).' if val and val > ENERGY_HIGH else 'Normal aralıkta.'}"
    if any(w in q for w in ['kalite', 'quality', 'skor']):
        val = data.get('production_quality_score')
        return f"Kalite skoru: {val}/100. {f'Düşük (<{QUALITY_LOW}).' if val and val < QUALITY_LOW else 'Kabul edilebilir seviyede.'}"
    if any(w in q for w in ['risk', 'tehlike', 'seviye']):
        return f"Risk seviyesi: {data.get('risk_level', '?').upper()}. Anomali skoru: {data.get('anomaly_score', '?')}"
    if any(w in q for w in ['ne yapmalı', 'ne yapilmali', 'öneri', 'oneri', 'aksiyon']):
        return _get_recommendation(data.get('risk_level', 'low'))
    return (
        "LLM API key tanımlı değil. Kural tabanlı cevap verebilmem için "
        "sıcaklık, titreşim, enerji, kalite veya risk hakkında soru sor."
    )


def _get_recommendation(priority: str) -> str:
    if priority == 'high':
        return "Hattı durdurarak bakım ekibini acil çağırın. Sıcaklık ve titreşim değerlerini kontrol edin."
    elif priority == 'medium':
        return "Bir sonraki bakım döngüsünde ilgili parametreleri inceleyin. Üretim çıktısını yakından takip edin."
    return "Standart izleme rutinine devam edin. Değerler yakın dönemde normale dönmezse bakım planlayın."
