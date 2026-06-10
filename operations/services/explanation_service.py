import os

SYSTEM_PROMPT = (
    "Sen üretim operasyonları için çalışan bir AI karar destek asistanısın. "
    "Aşağıdaki üretim kaydını teknik olmayan operasyon diliyle açıkla. "
    "Cevabın kısa, net ve aksiyon odaklı olsun. "
    "Riskin neden oluştuğunu, olası sebebi ve önerilen aksiyonu belirt."
)


def _detect_provider():
    """Return (provider, api_key) for the first available key, or (None, None)."""
    checks = [
        ('openai',     os.getenv('OPENAI_API_KEY')),
        ('anthropic',  os.getenv('ANTHROPIC_API_KEY')),
        ('deepseek',   os.getenv('DEEPSEEK_API_KEY')),
        ('groq',       os.getenv('GROQ_API_KEY')),
        ('gemini',     os.getenv('GEMINI_API_KEY')),
    ]
    for provider, key in checks:
        if key:
            return provider, key
    return None, None


def generate_explanation(data: dict) -> dict:
    provider, api_key = _detect_provider()
    if provider:
        try:
            return _llm_explanation(data, provider, api_key)
        except Exception:
            pass
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


def _call_llm(data: dict, provider: str, api_key: str) -> str:
    human_content = f"Üretim verisi: {data}"

    if provider == 'openai':
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model='gpt-4o-mini', api_key=api_key, temperature=0.3)
        return _langchain_invoke(llm, human_content)

    if provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model='claude-haiku-4-5-20251001', api_key=api_key, temperature=0.3)
        return _langchain_invoke(llm, human_content)

    if provider == 'deepseek':
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model='deepseek-chat',
            api_key=api_key,
            base_url='https://api.deepseek.com',
            temperature=0.3,
        )
        return _langchain_invoke(llm, human_content)

    if provider == 'groq':
        from langchain_groq import ChatGroq
        llm = ChatGroq(model='llama3-8b-8192', api_key=api_key, temperature=0.3)
        return _langchain_invoke(llm, human_content)

    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', google_api_key=api_key, temperature=0.3)
        return _langchain_invoke(llm, human_content)

    raise ValueError(f"Unknown provider: {provider}")


def _langchain_invoke(llm, human_content: str) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ])
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

    if temp and temp > 85:
        findings.append("Sıcaklık normalin üzerinde.")
        priority = 'high'
    if vibration and vibration > 7:
        findings.append("Titreşim seviyesi yüksek, makine zorlanması olabilir.")
        priority = 'high'
    if energy and energy > 65:
        findings.append("Enerji tüketimi üretim miktarına göre yüksek.")
        if priority == 'low':
            priority = 'medium'
    if quality and quality < 85:
        findings.append("Kalite skoru düşük.")
        if priority == 'low':
            priority = 'medium'
    if humidity and humidity > 70:
        findings.append("Nem seviyesi yüksek, hammadde veya ortam koşulları etkilenmiş olabilir.")
        if priority == 'low':
            priority = 'medium'
    if pressure and pressure > 5:
        findings.append("Basınç değeri normalin üzerinde.")
        if priority == 'low':
            priority = 'medium'
    if volume and volume < 60:
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
            return _call_llm_question(data, question, provider, api_key)
        except Exception:
            pass
    return _rule_based_answer(data, question)


def _call_llm_question(data: dict, question: str, provider: str, api_key: str) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    system = SystemMessage(content=(
        "Sen bir üretim operasyonları AI asistanısın. "
        "Sana bir üretim kaydının sensör verileri ve kullanıcının sorusu verilecek. "
        "Soruyu kısa, net ve Türkçe olarak cevapla. Teknik ama anlaşılır ol."
    ))
    human = HumanMessage(content=(
        f"Üretim kaydı:\n{data}\n\n"
        f"Kullanıcı sorusu: {question}"
    ))

    if provider == 'openai':
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model='gpt-4o-mini', api_key=api_key, temperature=0.3)
    elif provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model='claude-haiku-4-5-20251001', api_key=api_key, temperature=0.3)
    elif provider == 'deepseek':
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model='deepseek-chat', api_key=api_key,
                         base_url='https://api.deepseek.com', temperature=0.3)
    elif provider == 'groq':
        from langchain_groq import ChatGroq
        llm = ChatGroq(model='llama3-8b-8192', api_key=api_key, temperature=0.3)
    elif provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash',
                                     google_api_key=api_key, temperature=0.3)
    else:
        return _rule_based_answer(data, question)

    return llm.invoke([system, human]).content.strip()


def _rule_based_answer(data: dict, question: str) -> str:
    q = question.lower()
    if any(w in q for w in ['sıcaklık', 'sicaklik', 'temperature', 'ısı']):
        val = data.get('temperature')
        return f"Sıcaklık değeri: {val}°C. {'Normalin üzerinde (>85°C).' if val and val > 85 else 'Normal aralıkta.'}"
    if any(w in q for w in ['titreşim', 'titresim', 'vibration']):
        val = data.get('vibration_level')
        return f"Titreşim seviyesi: {val} mm/s. {'Yüksek (>7 mm/s), makine zorlanıyor olabilir.' if val and val > 7 else 'Normal aralıkta.'}"
    if any(w in q for w in ['enerji', 'energy', 'kwh']):
        val = data.get('energy_consumption')
        return f"Enerji tüketimi: {val} kWh. {'Yüksek (>65 kWh).' if val and val > 65 else 'Normal aralıkta.'}"
    if any(w in q for w in ['kalite', 'quality', 'skor']):
        val = data.get('production_quality_score')
        return f"Kalite skoru: {val}/100. {'Düşük (<85).' if val and val < 85 else 'Kabul edilebilir seviyede.'}"
    if any(w in q for w in ['risk', 'tehlike', 'seviye']):
        return f"Risk seviyesi: {data.get('risk_level', '?').upper()}. Anomali skoru: {data.get('anomaly_score', '?')}"
    if any(w in q for w in ['ne yapmalı', 'ne yapilmali', 'öneri', 'oneri', 'aksiyon']):
        return _get_recommendation(data.get('risk_level', 'low'))
    return ("LLM API key tanımlı değil. Kural tabanlı cevap verebilmem için "
            "sıcaklık, titreşim, enerji, kalite veya risk hakkında soru sor.")


def _get_recommendation(priority: str) -> str:
    if priority == 'high':
        return "Hattı durdurarak bakım ekibini acil çağırın. Sıcaklık ve titreşim değerlerini kontrol edin."
    elif priority == 'medium':
        return "Bir sonraki bakım döngüsünde ilgili parametreleri inceleyin. Üretim çıktısını yakından takip edin."
    return "Standart izleme rutinine devam edin. Değerler yakın dönemde normale dönmezse bakım planlayın."
