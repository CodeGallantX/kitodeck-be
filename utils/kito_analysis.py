import re
from datetime import datetime
import logging
from .constants import PROHIBITED_WORDS, SUSPICIOUS_PATTERNS

logger = logging.getLogger(__name__)

def analyze_text_content(text):
    """Enhanced text analysis for kito scam indicators"""
    if not text or not isinstance(text, str):
        return {
            'error': 'Invalid text input',
            'is_potential_kito': False,
            'risk_score': 0.0,
            'risk_level': 'low'
        }
    
    lower_text = text.lower()
    
    # Check for prohibited words with context awareness
    found_words = []
    for word in PROHIBITED_WORDS:
        if re.search(rf'\b{re.escape(word)}\b', lower_text):
            found_words.append(word)
    
    # Check for suspicious patterns with improved regex
    pattern_matches = []
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, lower_text, re.IGNORECASE):
            pattern_matches.append(pattern)
    
    # Enhanced risk scoring
    word_score = min(0.7, len(found_words) * 0.15)  # More weight for prohibited words
    pattern_score = min(0.3, len(pattern_matches) * 0.1)  # Increased pattern weight
    
    # Additional scoring factors
    urgency_score = 0.0
    if any(word in lower_text for word in ['urgent', 'immediately', 'asap', 'now']):
        urgency_score = 0.2
    
    secrecy_score = 0.0
    if any(word in lower_text for word in ['secret', 'private', 'confidential', 'dont tell']):
        secrecy_score = 0.15
    
    total_score = min(1.0, word_score + pattern_score + urgency_score + secrecy_score)
    
    # Determine risk level
    risk_level = "low"
    if total_score > 0.3:
        risk_level = "medium"
    if total_score > 0.6:
        risk_level = "high"
    if total_score > 0.85:
        risk_level = "critical"
    
    return {
        'is_potential_kito': total_score > 0.25,
        'risk_score': round(total_score, 2),
        'risk_level': risk_level,
        'prohibited_words': found_words,
        'suspicious_patterns': pattern_matches,
        'word_count': len(text.split()),
        'character_count': len(text),
        'analysis_version': '2.1'
    }

def check_conversation_signals(messages):
    """Enhanced conversation pattern analysis"""
    if not messages or not isinstance(messages, list):
        return {
            'error': 'Invalid messages input',
            'urgent_meetup_request': False,
            'location_change_request': False,
            'rapid_escalation': False,
            'excessive_secrecy': False,
            'financial_request': False
        }
    
    signals = {
        'urgent_meetup_request': False,
        'location_change_request': False,
        'rapid_escalation': False,
        'excessive_secrecy': False,
        'financial_request': False
    }
    
    # Combine all messages for analysis
    combined_text = " ".join([str(msg.get('content', '')) for msg in messages]).lower()
    
    # Check for urgent meetup requests
    urgent_phrases = [
        'meet now', 'come quickly', 'urgent meeting', 'asap',
        'right away', 'immediately', 'hurry up'
    ]
    if any(phrase in combined_text for phrase in urgent_phrases):
        signals['urgent_meetup_request'] = True
    
    # Check for location changes
    location_phrases = [
        'change location', 'different place', 'new address',
        'not here', 'go to', 'move to', 'another spot'
    ]
    if any(phrase in combined_text for phrase in location_phrases):
        signals['location_change_request'] = True
    
    # Check for financial requests
    financial_phrases = [
        'send money', 'need cash', 'bring money',
        'pay me', 'transfer funds', 'mobile money'
    ]
    if any(phrase in combined_text for phrase in financial_phrases):
        signals['financial_request'] = True
    
    # Check for excessive secrecy
    secrecy_phrases = [
        'our secret', 'between us', 'tell no one',
        'dont share', 'keep quiet', 'confidential'
    ]
    if any(phrase in combined_text for phrase in secrecy_phrases):
        signals['excessive_secrecy'] = True
    
    # Check message timestamps for rapid escalation
    if len(messages) >= 3:
        try:
            timestamps = [msg.get('timestamp') for msg in messages if 'timestamp' in msg]
            if len(timestamps) >= 3:
                try:
                    # Parse timestamps (assuming ISO format)
                    parsed_times = [datetime.fromisoformat(ts) for ts in timestamps]
                    time_diffs = [
                        (parsed_times[i+1] - parsed_times[i]).total_seconds() 
                        for i in range(len(parsed_times)-1)
                    ]
                    avg_diff = sum(time_diffs) / len(time_diffs)
                    
                    # If average time between messages is very short and convo mentions meeting
                    if avg_diff < 30 and any(word in combined_text for word in ['meet', 'meeting', 'location']):
                        signals['rapid_escalation'] = True
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing timestamps: {str(e)}")
        except Exception as e:
            logger.error(f"Error in timestamp analysis: {str(e)}")
    
    return signals