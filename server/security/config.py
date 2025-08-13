"""
Security configuration and utilities for the streaming backend server.
Contains security constants, patterns, and helper functions.
"""

import re
import html
import hashlib
from typing import List, Dict, Set, Any, Optional
from datetime import datetime, timedelta


class SecurityConfig:
    """Central security configuration"""
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = 100
    RATE_LIMIT_BURST_REQUESTS = 20
    RATE_LIMIT_WINDOW_SECONDS = 60
    
    # Request size limits
    MAX_REQUEST_SIZE_BYTES = 1024 * 1024  # 1MB
    MAX_TEXT_LENGTH = 10000
    MAX_CHAT_MESSAGE_LENGTH = 500
    MAX_USERNAME_LENGTH = 50
    MAX_BULK_TEXTS = 50
    MAX_CLIENT_INFO_SIZE = 1000
    
    # Content security
    MIN_TEXT_LENGTH = 1
    MIN_USERNAME_LENGTH = 2
    MAX_REPETITION_RATIO = 0.1  # 10% unique characters minimum
    MAX_REPETITION_THRESHOLD = 100  # Check repetition only for texts longer than this
    
    # Session and tracking
    REQUEST_ID_LENGTH = 36  # UUID length
    SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
    
    # Logging
    SECURITY_LOG_RETENTION_DAYS = 30
    MAX_LOG_ENTRY_LENGTH = 1000


class SecurityPatterns:
    """Security patterns for content validation"""
    
    # XSS and injection patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript\s*:',  # JavaScript protocols
        r'data\s*:\s*text/html',  # Data URLs with HTML
        r'vbscript\s*:',  # VBScript protocols
        r'on\w+\s*=',  # Event handlers (onclick, onload, etc.)
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(\s*["\']?\s*javascript',  # CSS url() with javascript
        r'<\s*iframe[^>]*>',  # Iframe tags
        r'<\s*object[^>]*>',  # Object tags
        r'<\s*embed[^>]*>',  # Embed tags
        r'<\s*form[^>]*>',  # Form tags
        r'<\s*input[^>]*>',  # Input tags
        r'eval\s*\(',  # Eval function calls
        r'setTimeout\s*\(',  # setTimeout calls
        r'setInterval\s*\(',  # setInterval calls
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+.*\s+set',
        r'--\s*$',  # SQL comments
        r'/\*.*\*/',  # SQL block comments
        r'xp_cmdshell',
        r'sp_executesql',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r';\s*(ls|dir|cat|type|echo|whoami|id)',
        r'\|\s*(ls|dir|cat|type|echo|whoami|id)',
        r'`[^`]+`',  # Backtick command substitution
        r'\$\([^)]+\)',  # Command substitution
        r'&&\s*(ls|dir|cat|type|echo)',
        r'\|\|\s*(ls|dir|cat|type|echo)',
    ]
    
    # Spam and suspicious content patterns
    SPAM_PATTERNS = [
        r'https?://[^\s]+\.(tk|ml|ga|cf|cc)',  # Suspicious TLDs
        r'bit\.ly|tinyurl|t\.co|goo\.gl',  # URL shorteners
        r'(?i)(buy|sell|cheap|free|win|prize).{0,20}(now|today|click|here)',
        r'(?i)(viagra|cialis|pharmacy|casino|poker|lottery)',
        r'(?i)(make\s+money|get\s+rich|work\s+from\s+home)',
        r'(?i)(click\s+here|visit\s+now|limited\s+time)',
        r'\$+\d+|\d+\$|€+\d+|\d+€',  # Money references
        r'[A-Z]{3,}\s+[A-Z]{3,}\s+[A-Z]{3,}',  # All caps spam
    ]
    
    # Hate speech indicators (basic patterns)
    HATE_SPEECH_PATTERNS = [
        r'(?i)\b(kill|die|death)\s+(yourself|urself|u)\b',
        r'(?i)\b(kys|kms)\b',  # Common abbreviations
        r'(?i)\b(nazi|hitler|holocaust)\b',
        r'(?i)\b(terrorist|terrorism)\b',
        r'(?i)\b(rape|molest)\b',
    ]
    
    # Excessive repetition patterns
    REPETITION_PATTERNS = [
        r'(.)\1{10,}',  # 10+ repeated characters
        r'(\w+\s+)\1{5,}',  # 5+ repeated words
        r'([!@#$%^&*()_+=\-\[\]{}|;:,.<>?])\1{10,}',  # 10+ repeated symbols
    ]


class SecurityFilters:
    """Security filtering and sanitization utilities"""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text input to remove potentially dangerous content.
        
        Args:
            text: Raw text input
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If text contains malicious content
        """
        if not text:
            return ""
        
        # Remove null bytes and control characters (except newlines, tabs, carriage returns)
        sanitized = ''.join(
            char for char in text 
            if ord(char) >= 32 or char in '\n\t\r'
        )
        
        # HTML escape to prevent XSS
        sanitized = html.escape(sanitized)
        
        # Check for malicious patterns
        SecurityFilters._check_malicious_patterns(sanitized)
        
        return sanitized
    
    @staticmethod
    def _check_malicious_patterns(text: str) -> None:
        """
        Check text for malicious patterns.
        
        Args:
            text: Text to check
            
        Raises:
            ValueError: If malicious patterns are found
        """
        text_lower = text.lower()
        
        # Check XSS patterns
        for pattern in SecurityPatterns.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                raise ValueError("Text contains potentially malicious content")
        
        # Check SQL injection patterns
        for pattern in SecurityPatterns.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError("Text contains potentially malicious content")
        
        # Check command injection patterns
        for pattern in SecurityPatterns.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError("Text contains potentially malicious content")
    
    @staticmethod
    def check_spam_patterns(text: str) -> bool:
        """
        Check if text contains spam patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if spam patterns are found
        """
        text_lower = text.lower()
        
        for pattern in SecurityPatterns.SPAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def check_hate_speech_patterns(text: str) -> bool:
        """
        Check if text contains hate speech patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if hate speech patterns are found
        """
        text_lower = text.lower()
        
        for pattern in SecurityPatterns.HATE_SPEECH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def check_excessive_repetition(text: str) -> bool:
        """
        Check if text contains excessive character or word repetition.
        
        Args:
            text: Text to check
            
        Returns:
            True if excessive repetition is found
        """
        # Only check texts longer than threshold
        if len(text) < SecurityConfig.MAX_REPETITION_THRESHOLD:
            return False
        
        # Check character diversity
        unique_chars = len(set(text.lower()))
        total_chars = len(text)
        diversity_ratio = unique_chars / total_chars
        
        if diversity_ratio < SecurityConfig.MAX_REPETITION_RATIO:
            return True
        
        # Check for repetition patterns
        for pattern in SecurityPatterns.REPETITION_PATTERNS:
            if re.search(pattern, text):
                return True
        
        return False
    
    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate and sanitize username.
        
        Args:
            username: Raw username
            
        Returns:
            Sanitized username
            
        Raises:
            ValueError: If username is invalid
        """
        if not username:
            raise ValueError("Username is required")
        
        # Basic sanitization
        sanitized = username.strip()
        
        # Length check
        if len(sanitized) < SecurityConfig.MIN_USERNAME_LENGTH:
            raise ValueError(f"Username must be at least {SecurityConfig.MIN_USERNAME_LENGTH} characters")
        
        if len(sanitized) > SecurityConfig.MAX_USERNAME_LENGTH:
            raise ValueError(f"Username must not exceed {SecurityConfig.MAX_USERNAME_LENGTH} characters")
        
        # Character validation (alphanumeric plus underscore and hyphen)
        if not re.match(r'^[a-zA-Z0-9_\-]+$', sanitized):
            raise ValueError("Username contains invalid characters")
        
        # Check reserved names
        reserved_names = {
            'admin', 'administrator', 'root', 'system', 'bot', 'moderator',
            'mod', 'null', 'undefined', 'anonymous', 'guest', 'user', 'test',
            'support', 'help', 'service', 'api', 'www', 'ftp', 'mail', 'email'
        }
        
        if sanitized.lower() in reserved_names:
            raise ValueError("Username is reserved")
        
        return sanitized
    
    @staticmethod
    def hash_ip_for_logging(ip: str) -> str:
        """
        Hash IP address for privacy-compliant logging.
        
        Args:
            ip: IP address
            
        Returns:
            Hashed IP address
        """
        # Use SHA-256 with a salt for IP hashing
        salt = "streaming_server_salt_2024"  # In production, use environment variable
        hash_input = f"{ip}{salt}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()[:16]  # First 16 chars for brevity
    
    @staticmethod
    def sanitize_log_data(data: Any, max_length: int = SecurityConfig.MAX_LOG_ENTRY_LENGTH) -> str:
        """
        Sanitize data for safe logging.
        
        Args:
            data: Data to log
            max_length: Maximum length of log entry
            
        Returns:
            Sanitized log string
        """
        # Convert to string
        log_str = str(data)
        
        # Truncate if too long
        if len(log_str) > max_length:
            log_str = log_str[:max_length - 3] + "..."
        
        # Remove sensitive patterns
        log_str = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', 'password=***', log_str, flags=re.IGNORECASE)
        log_str = re.sub(r'token["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', 'token=***', log_str, flags=re.IGNORECASE)
        log_str = re.sub(r'key["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', 'key=***', log_str, flags=re.IGNORECASE)
        
        # Remove control characters for log safety
        log_str = ''.join(char for char in log_str if ord(char) >= 32 or char in '\n\t')
        
        return log_str


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
    
    def is_allowed(self, client_id: str, max_requests: int = SecurityConfig.RATE_LIMIT_REQUESTS_PER_MINUTE) -> bool:
        """
        Check if request is allowed based on rate limiting.
        
        Args:
            client_id: Client identifier (e.g., IP address)
            max_requests: Maximum requests per minute
            
        Returns:
            True if request is allowed
        """
        current_time = datetime.now()
        
        # Check if IP is temporarily blocked
        if client_id in self.blocked_ips:
            if current_time < self.blocked_ips[client_id]:
                return False
            else:
                # Unblock expired IPs
                del self.blocked_ips[client_id]
        
        # Initialize client request history
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - timedelta(seconds=SecurityConfig.RATE_LIMIT_WINDOW_SECONDS)
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) >= max_requests:
            # Block IP for 1 minute
            self.blocked_ips[client_id] = current_time + timedelta(minutes=1)
            return False
        
        # Add current request
        self.requests[client_id].append(current_time)
        return True
    
    def get_remaining_requests(self, client_id: str, max_requests: int = SecurityConfig.RATE_LIMIT_REQUESTS_PER_MINUTE) -> int:
        """
        Get remaining requests for client.
        
        Args:
            client_id: Client identifier
            max_requests: Maximum requests per minute
            
        Returns:
            Number of remaining requests
        """
        if client_id not in self.requests:
            return max_requests
        
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=SecurityConfig.RATE_LIMIT_WINDOW_SECONDS)
        
        # Count recent requests
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]
        
        return max(0, max_requests - len(recent_requests))


# Global instances
security_config = SecurityConfig()
security_patterns = SecurityPatterns()
security_filters = SecurityFilters()
rate_limiter = RateLimiter()