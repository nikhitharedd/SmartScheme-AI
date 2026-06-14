from datetime import datetime


_INDIAN_STATES = {
    "Andhra Pradesh": {"te": "ఆంధ్ర ప్రదేశ్", "hi": "आंध्र प्रदेश"},
    "Arunachal Pradesh": {"te": "అరుణాచల్ ప్రదేశ్", "hi": "अरुणाचल प्रदेश"},
    "Assam": {"te": "అసోం", "hi": "असम"},
    "Bihar": {"te": "బీహార్", "hi": "बिहार"},
    "Chhattisgarh": {"te": "ఛత్తీస్‌గఢ్", "hi": "छत्तीसगढ़"},
    "Goa": {"te": "గోవా", "hi": "गोवा"},
    "Gujarat": {"te": "గుజరాత్", "hi": "गुजरात"},
    "Haryana": {"te": "హర్యానా", "hi": "हरियाणा"},
    "Himachal Pradesh": {"te": "హిమాచల్ ప్రదేశ్", "hi": "हिमाचल प्रदेश"},
    "Jharkhand": {"te": "జార్ఖండ్", "hi": "झारखंड"},
    "Karnataka": {"te": "కర్ణాటక", "hi": "कर्नाटक"},
    "Kerala": {"te": "కేరళ", "hi": "केरल"},
    "Madhya Pradesh": {"te": "మధ్య ప్రదేశ్", "hi": "मध्य प्रदेश"},
    "Maharashtra": {"te": "మహారాష్ట్ర", "hi": "महाराष्ट्र"},
    "Manipur": {"te": "మణిపూర్", "hi": "मणिपुर"},
    "Meghalaya": {"te": "మేఘాలయ", "hi": "मेघालय"},
    "Mizoram": {"te": "మిజోరం", "hi": "मिज़ोरम"},
    "Nagaland": {"te": "నాగాలాండ్", "hi": "नागालैंड"},
    "Odisha": {"te": "ఒడిశా", "hi": "ओडिशा"},
    "Punjab": {"te": "పంజాబ్", "hi": "पंजाब"},
    "Rajasthan": {"te": "రాజస్థాన్", "hi": "राजस्थान"},
    "Sikkim": {"te": "సిక్కిం", "hi": "सिक्किम"},
    "Tamil Nadu": {"te": "తమిళనాడు", "hi": "तमिलनाडु"},
    "Telangana": {"te": "తెలంగాణ", "hi": "तेलंगाना"},
    "Tripura": {"te": "త్రిపుర", "hi": "त्रिपुरा"},
    "Uttar Pradesh": {"te": "ఉత్తర ప్రదేశ్", "hi": "उत्तर प्रदेश"},
    "Uttarakhand": {"te": "ఉత్తరాఖండ్", "hi": "उत्तराखंड"},
    "West Bengal": {"te": "పశ్చిమ బెంగాల్", "hi": "पश्चिम बंगाल"},
    "Andaman and Nicobar Islands": {"te": "అండమాన్ నికోబార్ దీవులు", "hi": "अंडमान और निकोबार द्वीप समूह"},
    "Chandigarh": {"te": "చండీగఢ్", "hi": "चंडीगढ़"},
    "Dadra and Nagar Haveli and Daman and Diu": {"te": "దాద్రా నగర్ హవేలీ మరియు డామన్ డయ్యు", "hi": "दादरा और नगर हवेली और दमन और दीव"},
    "Delhi": {"te": "ఢిల్లీ", "hi": "दिल्ली"},
    "Jammu and Kashmir": {"te": "జమ్మూ కాశ్మీర్", "hi": "जम्मू और कश्मीर"},
    "Ladakh": {"te": "లడఖ్", "hi": "लद्दाख"},
    "Lakshadweep": {"te": "లక్షద్వీప్", "hi": "लक्षद्वीप"},
    "Puducherry": {"te": "పుదుచ్చేరి", "hi": "पुडुचेरी"},
}

_OCCUPATIONS = {
    "Farmer": {"te": "రైతు", "hi": "किसान"},
    "Agricultural Labourer": {"te": "వ్యవసాయ కూలీ", "hi": "कृषि मजदूर"},
    "Teacher": {"te": "ఉపాధ్యాయుడు", "hi": "शिक्षक"},
    "Student": {"te": "విద్యార్థి", "hi": "छात्र"},
    "Doctor": {"te": "వైద్యుడు", "hi": "डॉक्टर"},
    "Engineer": {"te": "ఇంజనీర్", "hi": "इंजीनियर"},
    "Government Employee": {"te": "ప్రభుత్వ ఉద్యోగి", "hi": "सरकारी कर्मचारी"},
    "Private Employee": {"te": "ప్రైవేటు ఉద్యోగి", "hi": "निजी कर्मचारी"},
    "Self Employed": {"te": "స్వయం ఉపాధి", "hi": "स्वरोजगार"},
    "Street Vendor": {"te": "వీధి వ్యాపారి", "hi": "सड़क विक्रेता"},
    "Fisherman": {"te": "చేపల వేటగాడు", "hi": "मछुआरा"},
    "Housewife": {"te": "గృహిణి", "hi": "गृहिणी"},
    "Retired": {"te": "పదవీ విరమణ", "hi": "सेवानिवृत्त"},
    "Unorganized Worker": {"te": "అసంఘటిత కార్మికుడు", "hi": "असंगठित कार्यकर्ता"},
    "Small Business Owner": {"te": "చిన్న వ్యాపారి", "hi": "छोटा व्यवसायी"},
    "Artist": {"te": "కళాకారుడు", "hi": "कलाकार"},
    "Nurse": {"te": "నర్సు", "hi": "नर्स"},
    "Lawyer": {"te": "న్యాయవాది", "hi": "वकील"},
    "Driver": {"te": "డ్రైవర్", "hi": "ड्राइवर"},
    "Construction Worker": {"te": "నిర్మాణ కార్మికుడు", "hi": "निर्माण मजदूर"},
}

_LOCALE_INFO = {
    "en": {
        "decimal_sep": ".",
        "thousand_sep": ",",
        "currency_symbol": "₹",
        "currency_format": "{symbol}{amount}",
        "date_format": "%d-%m-%Y",
        "locale": "en_IN",
    },
    "te": {
        "decimal_sep": ".",
        "thousand_sep": ",",
        "currency_symbol": "₹",
        "currency_format": "{symbol}{amount}",
        "date_format": "%d-%m-%Y",
        "locale": "te_IN",
    },
    "hi": {
        "decimal_sep": ".",
        "thousand_sep": ",",
        "currency_symbol": "₹",
        "currency_format": "{symbol}{amount}",
        "date_format": "%d-%m-%Y",
        "locale": "hi_IN",
    },
}

_SCRIPT_DIRECTION = {
    "en": "ltr",
    "te": "ltr",
    "hi": "ltr",
}


def format_currency(amount: float, lang: str = "en") -> str:
    info = _LOCALE_INFO.get(lang, _LOCALE_INFO["en"])
    symbol = info["currency_symbol"]

    if amount >= 10000000:
        crore = amount / 10000000
        formatted = f"{crore:.2f}"
        return f"{symbol}{formatted} crore"
    elif amount >= 100000:
        lakh = amount / 100000
        formatted = f"{lakh:.2f}"
        return f"{symbol}{formatted} lakh"

    formatted = f"{amount:,.2f}"
    return info["currency_format"].format(symbol=symbol, amount=formatted)


def format_number(number: float, lang: str = "en") -> str:
    return f"{number:,}"

def format_date(date_str: str, lang: str = "en") -> str:
    info = _LOCALE_INFO.get(lang, _LOCALE_INFO["en"])
    try:
        dt = datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return date_str
    return dt.strftime(info["date_format"])


def get_locale_info(lang: str) -> dict:
    return _LOCALE_INFO.get(lang, _LOCALE_INFO["en"])


def get_script_direction(lang: str) -> str:
    return _SCRIPT_DIRECTION.get(lang, "ltr")


def map_state_name(state_en: str, lang: str) -> str:
    if lang == "en":
        return state_en
    state_data = _INDIAN_STATES.get(state_en)
    if state_data is None:
        return state_en
    return state_data.get(lang, state_en)


def map_occupation(occupation: str, lang: str) -> str:
    if lang == "en":
        return occupation
    occ_data = _OCCUPATIONS.get(occupation)
    if occ_data is None:
        return occupation
    return occ_data.get(lang, occupation)
