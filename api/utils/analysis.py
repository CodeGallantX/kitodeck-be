# Text analysis utilities
PROHIBITED_WORDS = ['kito', 'scam', 'fraud', 'cheat', 'fake', 'phishing']

def analyze_text_content(text):
    """Analyze text for prohibited content"""
    lower_text = text.lower()
    found_words = [word for word in PROHIBITED_WORDS if word in lower_text]
    score = min(1.0, len(found_words) * 0.5)  # 0-1 scale
    
    return {
        'is_abusive': bool(found_words),
        'prohibited_words': found_words,
        'score': score,
        'word_count': len(text.split()),
        'character_count': len(text)
    }