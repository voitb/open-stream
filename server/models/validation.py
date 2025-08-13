"""
Comprehensive Pydantic validation models for secure API endpoints.
Implements input validation, sanitization, and security checks.
"""

import re
import html
from typing import Optional, Dict, Any, List, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic import StringConstraints
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported languages for text analysis"""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    AUTO = "auto"


class AnalysisMode(str, Enum):
    """Analysis modes for text processing"""
    BASIC = "basic"
    ADVANCED = "advanced"
    MODERATE = "moderate"
    COMPREHENSIVE = "comprehensive"


class TextAnalysisRequest(BaseModel):
    """
    Secure validation model for text analysis requests.
    Implements comprehensive input sanitization and validation.
    """
    
    # Text content with strict validation
    text: Annotated[str, StringConstraints(
        min_length=1,
        max_length=10000,
        strip_whitespace=True
    )] = Field(
        ...,
        description="Text to analyze (1-10000 characters)",
        example="This is a sample text for analysis"
    )
    
    # Optional analysis options
    language: SupportedLanguage = Field(
        default=SupportedLanguage.AUTO,
        description="Language of the text for optimized analysis"
    )
    
    mode: AnalysisMode = Field(
        default=AnalysisMode.BASIC,
        description="Analysis depth and features to include"
    )
    
    # Request metadata with validation
    include_sentiment: bool = Field(
        default=True,
        description="Include sentiment analysis in results"
    )
    
    include_toxicity: bool = Field(
        default=True,
        description="Include toxicity detection in results"
    )
    
    include_emotions: bool = Field(
        default=False,
        description="Include emotion detection (requires advanced mode)"
    )
    
    include_hate_speech: bool = Field(
        default=False,
        description="Include hate speech detection (requires comprehensive mode)"
    )
    
    # Client metadata (optional but logged for monitoring)
    client_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional client metadata for monitoring"
    )
    
    @field_validator('text')
    @classmethod
    def validate_and_sanitize_text(cls, v: str) -> str:
        """
        Comprehensive text validation and sanitization.
        Prevents XSS, injection attacks, and malicious content.
        """
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        
        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = ''.join(char for char in v if ord(char) >= 32 or char in '\n\t\r')
        
        # Check for suspicious patterns BEFORE HTML escaping
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocols
            r'data:text/html',  # Data URLs with HTML
            r'vbscript:',  # VBScript protocols
            r'on\w+\s*=',  # Event handlers
            r'expression\s*\(',  # CSS expression
            r'url\s*\(',  # CSS url() that might contain javascript:
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError("Text contains potentially malicious content")
        
        # HTML escape to prevent XSS (after suspicious pattern checking)
        sanitized = html.escape(sanitized)
        
        # Check for excessive repetition (potential DoS)
        if len(set(sanitized.lower())) < len(sanitized) / 10 and len(sanitized) > 100:
            raise ValueError("Text contains excessive character repetition")
        
        # Validate character encoding (ensure it's valid UTF-8)
        try:
            sanitized.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError("Text contains invalid UTF-8 characters")
        
        return sanitized
    
    @field_validator('client_info')
    @classmethod
    def validate_client_info(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate client info to prevent injection in logs"""
        if v is None:
            return v
        
        # Limit client info size
        if len(str(v)) > 1000:
            raise ValueError("Client info too large (max 1000 characters)")
        
        # Ensure it's a clean dictionary
        if not isinstance(v, dict):
            raise ValueError("Client info must be a dictionary")
        
        # Sanitize keys and values
        clean_info = {}
        for key, value in v.items():
            if not isinstance(key, str) or len(key) > 100:
                continue
            
            # Sanitize key and value
            clean_key = re.sub(r'[^\w\-_.]', '', str(key)[:100])
            clean_value = str(value)[:200] if value is not None else None
            
            if clean_key:
                clean_info[clean_key] = clean_value
        
        return clean_info
    
    @model_validator(mode='after')
    def validate_analysis_options(self) -> 'TextAnalysisRequest':
        """Validate analysis options consistency"""
        # Emotions require advanced or comprehensive mode
        if self.include_emotions and self.mode == AnalysisMode.BASIC:
            raise ValueError("Emotion detection requires advanced or comprehensive analysis mode")
        
        # Hate speech detection requires comprehensive mode
        if self.include_hate_speech and self.mode not in [AnalysisMode.COMPREHENSIVE]:
            raise ValueError("Hate speech detection requires comprehensive analysis mode")
        
        return self
    
    model_config = ConfigDict(
        # Validate on assignment to catch issues early
        validate_assignment=True,
        # Use enum values in JSON schema
        use_enum_values=True,
        # JSON schema extra configuration
        json_schema_extra={
            "example": {
                "text": "This is a positive message about streaming!",
                "language": "en",
                "mode": "basic",
                "include_sentiment": True,
                "include_toxicity": True,
                "include_emotions": False,
                "include_hate_speech": False,
                "client_info": {
                    "version": "1.0.0",
                    "platform": "web"
                }
            }
        }
    )


class ChatMessageRequest(BaseModel):
    """
    Validation model for chat message requests.
    Used for real-time chat analysis and moderation.
    """
    
    message: Annotated[str, StringConstraints(
        min_length=1,
        max_length=500,
        strip_whitespace=True
    )] = Field(
        ...,
        description="Chat message content (1-500 characters)",
        example="Hello everyone! How is the stream going?"
    )
    
    username: Annotated[str, StringConstraints(
        min_length=2,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_\-]+$'
    )] = Field(
        ...,
        description="Username (2-50 characters, alphanumeric plus _ and -)",
        example="stream_viewer_123"
    )
    
    channel_id: Optional[Annotated[str, StringConstraints(
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-]+$'
    )]] = Field(
        default=None,
        description="Channel or room identifier",
        example="general_chat"
    )
    
    timestamp: Optional[int] = Field(
        default=None,
        description="Message timestamp (Unix timestamp)",
        ge=0,  # Must be positive
        example=1642694400
    )
    
    @field_validator('message')
    @classmethod
    def validate_chat_message(cls, v: str) -> str:
        """Validate and sanitize chat message"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        
        # Remove control characters except newlines
        sanitized = ''.join(char for char in v if ord(char) >= 32 or char == '\n')
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Check for spam patterns
        if re.search(r'(.)\1{10,}', sanitized):  # 10+ repeated characters
            raise ValueError("Message contains excessive character repetition")
        
        # Check for common spam patterns
        spam_patterns = [
            r'https?://[^\s]+\.(tk|ml|ga|cf)',  # Suspicious TLDs
            r'bit\.ly|tinyurl|t\.co',  # URL shorteners (be cautious)
            r'(?i)(buy|sell|cheap|free|win|prize).{0,20}(now|today|click)',
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError("Message contains potential spam content")
        
        return sanitized
    
    @field_validator('username')
    @classmethod
    def validate_username_security(cls, v: str) -> str:
        """Additional username security validation"""
        if not v:
            raise ValueError("Username is required")
        
        # Check for reserved names
        reserved_names = {
            'admin', 'administrator', 'root', 'system', 'bot', 'mod', 'moderator',
            'null', 'undefined', 'anonymous', 'guest', 'user', 'test'
        }
        
        if v.lower() in reserved_names:
            raise ValueError("Username is reserved")
        
        return v
    
    model_config = ConfigDict(
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "message": "Great stream! Thanks for the content!",
                "username": "viewer_123",
                "channel_id": "general_chat",
                "timestamp": 1642694400
            }
        }
    )


class BulkAnalysisRequest(BaseModel):
    """
    Validation model for bulk text analysis requests.
    Includes rate limiting and batch size constraints.
    """
    
    texts: List[Annotated[str, StringConstraints(min_length=1, max_length=1000)]] = Field(
        ...,
        description="List of texts to analyze",
        min_items=1,
        max_items=50  # Limit batch size
    )
    
    mode: AnalysisMode = Field(
        default=AnalysisMode.BASIC,
        description="Analysis mode for all texts"
    )
    
    include_sentiment: bool = Field(default=True)
    include_toxicity: bool = Field(default=True)
    
    @field_validator('texts')
    @classmethod
    def validate_texts_list(cls, v: List[str]) -> List[str]:
        """Validate each text in the list"""
        if len(v) == 0:
            raise ValueError("At least one text is required")
        
        # Apply same validation as single text analysis
        validated_texts = []
        for text in v:
            # Apply same validation logic as TextAnalysisRequest
            # Since we can't directly call the classmethod, we'll replicate the logic
            if not text or not text.strip():
                raise ValueError("Text cannot be empty or only whitespace")
            
            # Remove null bytes and control characters (except newlines and tabs)
            sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
            
            # Check for suspicious patterns BEFORE HTML escaping
            import re
            suspicious_patterns = [
                r'<script[^>]*>.*?</script>',  # Script tags
                r'javascript:',  # JavaScript protocols
                r'data:text/html',  # Data URLs with HTML
                r'vbscript:',  # VBScript protocols
                r'on\w+\s*=',  # Event handlers
                r'expression\s*\(',  # CSS expression
                r'url\s*\(',  # CSS url() that might contain javascript:
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    raise ValueError("Text contains potentially malicious content")
            
            # HTML escape to prevent XSS (after suspicious pattern checking)
            import html
            sanitized = html.escape(sanitized)
            
            # Check for excessive repetition (potential DoS)
            if len(set(sanitized.lower())) < len(sanitized) / 10 and len(sanitized) > 100:
                raise ValueError("Text contains excessive character repetition")
            
            # Validate character encoding (ensure it's valid UTF-8)
            try:
                sanitized.encode('utf-8')
            except UnicodeEncodeError:
                raise ValueError("Text contains invalid UTF-8 characters")
            
            validated_text = sanitized
            validated_texts.append(validated_text)
        
        return validated_texts
    
    model_config = ConfigDict(
        validate_assignment=True
    )


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service status")
    port: int = Field(..., description="Service port")
    ai_enabled: bool = Field(..., description="AI models availability")
    version: str = Field(..., description="Service version")
    models_loaded: Dict[str, bool] = Field(default={}, description="Individual model status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class AnalysisResponse(BaseModel):
    """Comprehensive response model for text analysis"""
    text: str = Field(..., description="Original analyzed text")
    language_detected: Optional[str] = Field(None, description="Detected language")
    
    # Core analysis results
    toxic: bool = Field(default=False, description="Is text toxic")
    toxicity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Toxicity confidence score")
    
    sentiment: str = Field(default="neutral", description="Sentiment classification")
    sentiment_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Sentiment confidence score")
    
    # Optional advanced results
    emotions: Optional[Dict[str, float]] = Field(None, description="Emotion detection results")
    hate_speech: Optional[bool] = Field(None, description="Hate speech detection")
    hate_speech_score: Optional[float] = Field(None, description="Hate speech confidence")
    
    # Metadata
    ai_enabled: bool = Field(..., description="Whether AI models were used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_versions: Dict[str, str] = Field(default={}, description="Model versions used")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "This is a positive message!",
                "language_detected": "en",
                "toxic": False,
                "toxicity_score": 0.05,
                "sentiment": "positive",
                "sentiment_score": 0.92,
                "emotions": {
                    "joy": 0.85,
                    "anger": 0.02,
                    "fear": 0.01,
                    "sadness": 0.03
                },
                "ai_enabled": True,
                "processing_time_ms": 145.2,
                "model_versions": {
                    "toxicity": "unitary/toxic-bert",
                    "sentiment": "nlptown/bert-base-multilingual-uncased-sentiment"
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standardized error response model following RFC 9457"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: Optional[str] = Field(None, description="Error timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Input validation failed",
                "details": {
                    "field": "text",
                    "issue": "Text contains potentially malicious content"
                },
                "request_id": "req_12345",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )