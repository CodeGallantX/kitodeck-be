from django.utils.translation import gettext_lazy as _

# Security Analysis Constants
PROHIBITED_WORDS = [
    'kito', 'scam', 'fraud', 'cheat', 'fake', 'phishing',
    'blackmail', 'extortion', 'emergency', 'robbery', 'ambush',
    'setup', 'trap', 'gang', 'danger', 'threat', 'ransom',
    'bait', 'lure', 'decoy', 'meet-up scam', 'dating scam',
    'catfish', 'impersonating', 'kidnap', 'hijack', 'attack'
]

SUSPICIOUS_PATTERNS = [
    r'send money', r'emergency situation', r'need help urgent',
    r'meet( me)? (at|in) .{1,20}(secluded|private|isolated)',
    r'don\'t tell anyone', r'keep (this|it) secret',
    r'change (of )?location', r'come alone', r'no friends',
    r'urgent meeting', r'quick meetup', r'need cash',
    r'wire transfer', r'bank details', r'account number',
    r'mobile money', r'pay me', r'urgent help needed'
]

RISK_THRESHOLDS = {
    'low': 0.3,
    'medium': 0.6,
    'high': 0.85
}

RISK_LEVEL_CHOICES = [
    ('low', _('Low Risk')),
    ('medium', _('Medium Risk')),
    ('high', _('High Risk')),
    ('critical', _('Critical Risk'))
]

# Email Constants
EMAIL_TEMPLATES = {
    'WELCOME': 'emails/welcome.html',
    'SAFETY_ALERT': 'emails/safety_alert.html',
    'PASSWORD_RESET': 'emails/password_reset.html'
}

EMAIL_SUBJECTS = {
    'WELCOME': _('Welcome to KitoDeck AI Protection'),
    'SAFETY_ALERT': _('Security Alert: Potential Risk Detected'),
    'PASSWORD_RESET': _('Password Reset Request')
}

# Application Constants
MAX_TEXT_LENGTH = 5000
MAX_IMAGE_SIZE_MB = 5
MAX_CONVERSATION_MESSAGES = 100
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Error Messages
ERROR_MESSAGES = {
    'INVALID_CREDENTIALS': _('Invalid email or password.'),
    'ACCOUNT_LOCKED': _('Account temporarily locked due to too many failed attempts.'),
    'EMAIL_IN_USE': _('This email address is already in use.'),
    'USERNAME_IN_USE': _('This username is already taken.'),
    'INVALID_TOKEN': _('Invalid or expired token.'),
    'PERMISSION_DENIED': _('You do not have permission to perform this action.')
}