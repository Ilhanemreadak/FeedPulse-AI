import os


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
    }


def _get_recommendation(priority: str) -> str:
    if priority == 'high':
        return "Hattı durdurarak bakım ekibini acil çağırın. Sıcaklık ve titreşim değerlerini kontrol edin."
    elif priority == 'medium':
        return "Bir sonraki bakım döngüsünde ilgili parametreleri inceleyin. Üretim çıktısını yakından takip edin."
    return "Standart izleme rutinine devam edin. Değerler yakın dönemde normale dönmezse bakım planlayın."


def generate_explanation(data: dict) -> dict:
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
    if api_key:
        try:
            return _llm_explanation(data, api_key)
        except Exception:
            pass
    return _rule_based_explanation(data)


def _llm_explanation(data: dict, api_key: str) -> dict:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage

    llm = ChatOpenAI(model='gpt-3.5-turbo', api_key=api_key, temperature=0.3)
    system_msg = SystemMessage(content=(
        "Sen üretim operasyonları için çalışan bir AI karar destek asistanısın. "
        "Aşağıdaki üretim kaydını teknik olmayan operasyon diliyle açıkla. "
        "Cevabın kısa, net ve aksiyon odaklı olsun. "
        "Riskin neden oluştuğunu, olası sebebi ve önerilen aksiyonu belirt."
    ))
    human_msg = HumanMessage(content=f"Üretim verisi: {data}")
    response = llm.invoke([system_msg, human_msg])
    text = response.content.strip()
    return {
        'diagnosis': text[:200],
        'possible_reason': 'LLM tarafından analiz edildi.',
        'recommendation': text,
        'priority': 'medium',
    }
