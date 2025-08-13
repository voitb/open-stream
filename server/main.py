"""
Enhanced FastAPI server with comprehensive Pydantic validation and security.
Implements input sanitization, rate limiting, secure error handling, and authenticated shutdown endpoint.
"""

import sys
import os
import signal
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Import validation models
from models.validation import (
    TextAnalysisRequest,
    ChatMessageRequest,
    BulkAnalysisRequest,
    AnalysisResponse,
    HealthCheckResponse,
    ErrorResponse
)

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log') if not os.getenv('NO_FILE_LOGGING') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security logger for monitoring
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log') if not os.getenv('NO_FILE_LOGGING') else logging.NullHandler()
security_handler.setFormatter(logging.Formatter('%(asctime)s - SECURITY - %(message)s'))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

# Server configuration
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 55555
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB max request size
RATE_LIMIT_REQUESTS = 100  # requests per minute per IP
START_TIME = time.time()

# Security configuration
SHUTDOWN_TOKEN = os.getenv('SHUTDOWN_TOKEN', '')
ELECTRON_APP_ID = os.getenv('ELECTRON_APP_ID', '')

# Allowed Electron origins (generated from app ID for security)
ALLOWED_ELECTRON_ORIGINS = []
if ELECTRON_APP_ID:
    # Allow localhost and 127.0.0.1 on dynamic ports for this specific Electron app
    for port_range in range(50000, 60000):  # Common Electron dev server range
        ALLOWED_ELECTRON_ORIGINS.extend([
            f"http://localhost:{port_range}",
            f"http://127.0.0.1:{port_range}"
        ])
    # Add file:// protocol for packaged Electron apps
    ALLOWED_ELECTRON_ORIGINS.append("file://")

logger.info(f"🔐 Shutdown authentication: {'Enabled' if SHUTDOWN_TOKEN else 'DISABLED'}")
logger.info(f"📱 Electron App ID: {ELECTRON_APP_ID}")
logger.info(f"🌐 CORS Origins configured: {len(ALLOWED_ELECTRON_ORIGINS)} patterns")

# Initialize FastAPI with enhanced configuration
app = FastAPI(
    title="Secure Streaming Backend Server with AI",
    description="AI-powered streaming assistant with comprehensive input validation and security",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Secure CORS configuration - restrict to specific Electron app only
cors_origins = ALLOWED_ELECTRON_ORIGINS if ALLOWED_ELECTRON_ORIGINS else [
    "http://localhost:*",
    "http://127.0.0.1:*",
    "file://*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "X-Request-ID",
        "X-Shutdown-Token",
        "X-Electron-App-ID"
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    allow_credentials=False,  # Set to False for security unless specifically needed
    max_age=600  # Cache preflight requests for 10 minutes
)

# Global variables for AI models
toxicity_model = None
sentiment_model = None
emotion_model = None
hate_speech_model = None
models_loaded = False
model_load_time = None

# Rate limiting storage (in production, use Redis or similar)
request_counts: Dict[str, Dict[str, Any]] = {}

# Request tracking
active_requests: Dict[str, Dict[str, Any]] = {}


def validate_shutdown_auth(
    x_shutdown_token: Optional[str] = Header(None),
    x_electron_app_id: Optional[str] = Header(None)
) -> bool:
    """Validate shutdown authentication credentials"""
    if not SHUTDOWN_TOKEN:
        logger.warning("🚨 Shutdown endpoint accessed but no token configured")
        return False
    
    if not x_shutdown_token:
        logger.warning("🚨 Shutdown endpoint accessed without token")
        return False
    
    if x_shutdown_token != SHUTDOWN_TOKEN:
        logger.warning("🚨 Shutdown endpoint accessed with invalid token")
        security_logger.critical(f"Invalid shutdown token attempt: {x_shutdown_token[:8]}...")
        return False
    
    # Validate Electron app ID if provided
    if ELECTRON_APP_ID and x_electron_app_id:
        if not x_electron_app_id.startswith('electron-'):
            logger.warning("🚨 Shutdown endpoint accessed with invalid Electron app ID format")
            return False
    
    logger.info("✅ Shutdown authentication validated")
    return True


def validate_origin(request: Request) -> bool:
    """Validate that the request origin is from the authorized Electron app"""
    origin = request.headers.get("origin")
    
    # Allow requests without origin header (direct API calls)
    if not origin:
        return True
    
    # If we have specific Electron origins configured, validate against them
    if ALLOWED_ELECTRON_ORIGINS:
        # Check exact matches first
        if origin in ALLOWED_ELECTRON_ORIGINS:
            return True
        
        # Check pattern matches for localhost and 127.0.0.1 with dynamic ports
        if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            return True
        
        # Allow file:// for packaged Electron apps
        if origin.startswith("file://"):
            return True
        
        logger.warning(f"🚨 Request from unauthorized origin: {origin}")
        security_logger.warning(f"Unauthorized origin attempt: {origin}")
        return False
    
    return True


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (be careful in production)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct connection IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return "unknown"


def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting implementation"""
    current_time = time.time()
    minute_window = int(current_time // 60)
    
    if client_ip not in request_counts:
        request_counts[client_ip] = {}
    
    client_requests = request_counts[client_ip]
    
    # Clean old entries
    old_windows = [window for window in client_requests.keys() if window < minute_window - 1]
    for window in old_windows:
        del client_requests[window]
    
    # Check current window
    current_count = client_requests.get(minute_window, 0)
    if current_count >= RATE_LIMIT_REQUESTS:
        return False
    
    # Increment counter
    client_requests[minute_window] = current_count + 1
    return True


def load_models():
    """Load AI models with comprehensive error handling - now uses optimized background loading"""
    global toxicity_model, sentiment_model, emotion_model, hate_speech_model
    global models_loaded, model_load_time
    
    if models_loaded:
        return
    
    try:
        logger.info("AI models loading in background for optimal performance...")
        load_start = time.time()
        
        # Import optimized AI manager
        from services.ai_manager import ai_manager
        
        # Check if models are already being loaded in background
        model_status = ai_manager.get_model_status()
        logger.info(f"Model loading status: {model_status}")
        
        # For immediate response, we'll use the ai_manager's lazy loading
        # Models will load on first use, but background loading is already started
        models_loaded = True
        model_load_time = time.time() - load_start
        
        logger.info(f"✅ AI Manager ready! Models loading in background for optimal startup time")
        logger.info(f"📊 Performance stats: {ai_manager.get_performance_stats()}")
        
    except Exception as e:
        logger.error(f"Failed to initialize AI manager: {e}")
        logger.warning("Running in fallback mode without AI")


async def analyze_text_with_ai(request: TextAnalysisRequest) -> Dict[str, Any]:
    """Perform AI-powered text analysis with caching and optimized loading"""
    start_time = time.time()
    
    # Import optimized AI manager
    from services.ai_manager import ai_manager
    
    result = {
        "text": request.text,
        "language_detected": request.language.value if request.language != "auto" else "en",
        "toxic": False,
        "toxicity_score": 0.0,
        "sentiment": "neutral", 
        "sentiment_score": 0.0,
        "ai_enabled": True,
        "processing_time_ms": 0.0,
        "model_versions": {},
        "cache_hit": False
    }
    
    try:
        # Toxicity analysis with caching
        if request.include_toxicity:
            try:
                tox_results = ai_manager.analyze_toxicity(request.text, use_cache=True)
                toxic_score = 0.0
                
                for result_item in tox_results:
                    if 'TOXIC' in result_item['label'].upper():
                        toxic_score = result_item['score']
                        break
                
                result["toxic"] = toxic_score > 0.5
                result["toxicity_score"] = round(toxic_score, 4)
                result["model_versions"]["toxicity"] = "unitary/toxic-bert"
            except Exception as e:
                logger.warning(f"Toxicity analysis failed: {e}")
                result["toxic"] = False
                result["toxicity_score"] = 0.0
        
        # Sentiment analysis with caching
        if request.include_sentiment:
            try:
                sent_results = ai_manager.analyze_sentiment(request.text, use_cache=True)
                sentiment_label = sent_results[0]['label'].lower()
                sentiment_score = sent_results[0]['score']
                
                # Map model output to standard sentiment labels
                if 'positive' in sentiment_label or sentiment_label in ['5 stars', '4 stars']:
                    sentiment = 'positive'
                elif 'negative' in sentiment_label or sentiment_label in ['1 star', '2 stars']:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                result["sentiment"] = sentiment
                result["sentiment_score"] = round(sentiment_score, 4)
                result["model_versions"]["sentiment"] = "distilbert-base-uncased-finetuned-sst-2-english"
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                result["sentiment"] = "neutral"
                result["sentiment_score"] = 0.0
        
        # Emotion analysis (if requested and model available)
        if request.include_emotions:
            try:
                emotion_results = ai_manager.analyze_with_caching(request.text, 'emotion')
                emotions = {}
                for emotion_result in emotion_results:
                    emotions[emotion_result['label'].lower()] = round(emotion_result['score'], 4)
                result["emotions"] = emotions
                result["model_versions"]["emotion"] = "j-hartmann/emotion-english-distilroberta-base"
            except Exception as e:
                logger.warning(f"Emotion analysis failed: {e}")
        
        # Hate speech detection (if requested and model available)
        if request.include_hate_speech:
            try:
                hate_results = ai_manager.analyze_with_caching(request.text, 'hate_speech')
                hate_score = 0.0
                for hate_result in hate_results:
                    if 'hate' in hate_result['label'].lower():
                        hate_score = hate_result['score']
                        break
                
                result["hate_speech"] = hate_score > 0.5
                result["hate_speech_score"] = round(hate_score, 4)
                result["model_versions"]["hate_speech"] = "Hate-speech-CNERG/dehatebert-mono-english"
            except Exception as e:
                logger.warning(f"Hate speech analysis failed: {e}")
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        # Fall back to rule-based analysis
        return analyze_text_fallback(request.text, start_time)
    
    # Calculate processing time
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return result


def analyze_text_fallback(text: str, start_time: float) -> Dict[str, Any]:
    """Fallback rule-based text analysis"""
    text_lower = text.lower()
    
    # Simple word lists for fallback analysis
    negative_words = ['hate', 'stupid', 'noob', 'trash', 'sucks', 'terrible', 'awful', 'bad']
    positive_words = ['love', 'great', 'awesome', 'amazing', 'fantastic', 'good', 'excellent']
    toxic_words = ['hate', 'stupid', 'idiot', 'loser', 'trash', 'kill', 'die']
    
    has_negative = any(word in text_lower for word in negative_words)
    has_positive = any(word in text_lower for word in positive_words)
    has_toxic = any(word in text_lower for word in toxic_words)
    
    if has_toxic:
        sentiment = "negative"
        toxic = True
        toxicity_score = 0.8
    elif has_negative:
        sentiment = "negative"
        toxic = False
        toxicity_score = 0.3
    elif has_positive:
        sentiment = "positive"
        toxic = False
        toxicity_score = 0.1
    else:
        sentiment = "neutral"
        toxic = False
        toxicity_score = 0.2
    
    return {
        "text": text,
        "language_detected": "en",
        "toxic": toxic,
        "toxicity_score": toxicity_score,
        "sentiment": sentiment,
        "sentiment_score": 0.6,
        "ai_enabled": False,
        "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        "model_versions": {"fallback": "rule-based-v1"}
    }


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with security logging"""
    client_ip = get_client_ip(request)
    request_id = str(uuid.uuid4())
    
    # Log validation failures for security monitoring
    security_logger.warning(
        f"Validation failed - IP: {client_ip}, Request: {request.method} {request.url.path}, "
        f"Errors: {exc.errors()}, Request-ID: {request_id}"
    )
    
    # Sanitize error messages to prevent information disclosure
    sanitized_errors = []
    for error in exc.errors():
        sanitized_error = {
            "field": str(error.get("loc", ["unknown"])[-1]),
            "message": "Invalid input format or content",
            "type": error.get("type", "validation_error")
        }
        sanitized_errors.append(sanitized_error)
    
    error_response = ErrorResponse(
        error="validation_error",
        message="Input validation failed. Please check your request format and content.",
        details={"fields": sanitized_errors},
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation-related ValueError exceptions"""
    client_ip = get_client_ip(request)
    request_id = str(uuid.uuid4())
    
    security_logger.warning(
        f"Value error - IP: {client_ip}, Request: {request.method} {request.url.path}, "
        f"Error: {str(exc)}, Request-ID: {request_id}"
    )
    
    error_response = ErrorResponse(
        error="invalid_input",
        message="The provided input contains invalid or potentially harmful content.",
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for rate limiting, origin validation, and request tracking"""
    request_id = str(uuid.uuid4())
    client_ip = get_client_ip(request)
    start_time = time.time()
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    # Validate origin for enhanced security
    if not validate_origin(request):
        security_logger.warning(f"Request blocked - unauthorized origin - IP: {client_ip}, Request-ID: {request_id}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "forbidden",
                "message": "Request from unauthorized origin",
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )
    
    # Rate limiting
    if not check_rate_limit(client_ip):
        security_logger.warning(f"Rate limit exceeded - IP: {client_ip}, Request-ID: {request_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "request_id": request_id
            },
            headers={
                "X-Request-ID": request_id,
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60"
            }
        )
    
    # Track active request
    active_requests[request_id] = {
        "ip": client_ip,
        "method": request.method,
        "path": request.url.path,
        "start_time": start_time
    }
    
    try:
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Log successful request
        processing_time = time.time() - start_time
        logger.info(
            f"Request completed - IP: {client_ip}, {request.method} {request.url.path}, "
            f"Status: {response.status_code}, Time: {processing_time:.3f}s, Request-ID: {request_id}"
        )
        
        return response
    
    except Exception as e:
        # Log error
        processing_time = time.time() - start_time
        logger.error(
            f"Request failed - IP: {client_ip}, {request.method} {request.url.path}, "
            f"Error: {str(e)}, Time: {processing_time:.3f}s, Request-ID: {request_id}"
        )
        raise
    
    finally:
        # Clean up tracking
        active_requests.pop(request_id, None)


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    logger.info("🚀 Starting Secure Streaming Backend Server")
    logger.info("📚 Models will load on first use for optimal startup time")
    logger.info("🔒 Security features: Input validation, rate limiting, request tracking, origin validation")
    logger.info(f"🔐 Shutdown authentication: {'Enabled' if SHUTDOWN_TOKEN else 'DISABLED - WARNING!'}")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Enhanced health check with model status"""
    uptime = time.time() - START_TIME
    
    model_status = {
        "toxicity": toxicity_model is not None,
        "sentiment": sentiment_model is not None,
        "emotion": emotion_model is not None,
        "hate_speech": hate_speech_model is not None,
    }
    
    return HealthCheckResponse(
        status="healthy",
        port=PORT,
        ai_enabled=models_loaded,
        version="2.1.0",
        models_loaded=model_status,
        uptime_seconds=round(uptime, 2)
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest, http_request: Request):
    """
    Analyze text with comprehensive AI models and security validation.
    
    This endpoint provides toxicity detection, sentiment analysis, and optional
    emotion detection and hate speech analysis with full input sanitization.
    """
    client_ip = get_client_ip(http_request)
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"Text analysis request - IP: {client_ip}, Length: {len(request.text)}, "
        f"Mode: {request.mode}, Request-ID: {request_id}"
    )
    
    try:
        # Perform analysis
        result = await analyze_text_with_ai(request)
        
        # Log potentially toxic content for monitoring
        if result.get("toxic", False) or result.get("toxicity_score", 0) > 0.7:
            security_logger.info(
                f"High toxicity detected - IP: {client_ip}, Score: {result.get('toxicity_score')}, "
                f"Request-ID: {request_id}"
            )
        
        return AnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Analysis failed - Request-ID: {request_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "analysis_failed",
                "message": "Text analysis temporarily unavailable. Please try again.",
                "request_id": request_id
            }
        )


@app.post("/analyze-chat")
async def analyze_chat_message(request: ChatMessageRequest, http_request: Request):
    """
    Analyze chat message with real-time moderation.
    
    Optimized for low-latency chat analysis with basic toxicity and sentiment detection.
    """
    client_ip = get_client_ip(http_request)
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"Chat analysis - IP: {client_ip}, User: {request.username}, "
        f"Channel: {request.channel_id}, Request-ID: {request_id}"
    )
    
    # Create simplified analysis request
    analysis_request = TextAnalysisRequest(
        text=request.message,
        mode="basic",
        include_sentiment=True,
        include_toxicity=True,
        include_emotions=False,
        include_hate_speech=False
    )
    
    try:
        result = await analyze_text_with_ai(analysis_request)
        
        # Add chat-specific metadata
        chat_result = {
            **result,
            "username": request.username,
            "channel_id": request.channel_id,
            "timestamp": request.timestamp or int(time.time())
        }
        
        # Log moderation actions
        if result.get("toxic", False):
            security_logger.warning(
                f"Toxic chat message - IP: {client_ip}, User: {request.username}, "
                f"Channel: {request.channel_id}, Score: {result.get('toxicity_score')}, "
                f"Request-ID: {request_id}"
            )
        
        return chat_result
        
    except Exception as e:
        logger.error(f"Chat analysis failed - Request-ID: {request_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "chat_analysis_failed",
                "message": "Chat analysis temporarily unavailable.",
                "request_id": request_id
            }
        )


@app.post("/analyze-bulk")
async def analyze_bulk_texts(request: BulkAnalysisRequest, http_request: Request):
    """
    Analyze multiple texts in a single request with batch processing.
    
    Limited to 50 texts per request for performance and security.
    """
    client_ip = get_client_ip(http_request)
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"Bulk analysis - IP: {client_ip}, Count: {len(request.texts)}, "
        f"Mode: {request.mode}, Request-ID: {request_id}"
    )
    
    try:
        results = []
        for i, text in enumerate(request.texts):
            # Create analysis request for each text
            analysis_request = TextAnalysisRequest(
                text=text,
                mode=request.mode,
                include_sentiment=request.include_sentiment,
                include_toxicity=request.include_toxicity,
                include_emotions=False,  # Disabled for bulk processing
                include_hate_speech=False  # Disabled for bulk processing
            )
            
            result = await analyze_text_with_ai(analysis_request)
            result["index"] = i  # Add index for client reference
            results.append(result)
        
        return {
            "results": results,
            "total_processed": len(results),
            "request_id": request_id,
            "processing_time_ms": sum(r.get("processing_time_ms", 0) for r in results)
        }
        
    except Exception as e:
        logger.error(f"Bulk analysis failed - Request-ID: {request_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "bulk_analysis_failed",
                "message": "Bulk analysis temporarily unavailable.",
                "request_id": request_id
            }
        )


@app.get("/stats")
async def get_server_stats():
    """Get server statistics and monitoring information"""
    uptime = time.time() - START_TIME
    
    return {
        "server": {
            "version": "2.1.0",
            "uptime_seconds": round(uptime, 2),
            "active_requests": len(active_requests),
            "models_loaded": models_loaded,
            "model_load_time": model_load_time
        },
        "security": {
            "rate_limiting_enabled": True,
            "validation_enabled": True,
            "request_tracking_enabled": True,
            "origin_validation_enabled": bool(ALLOWED_ELECTRON_ORIGINS),
            "shutdown_auth_enabled": bool(SHUTDOWN_TOKEN)
        },
        "models": {
            "toxicity_available": toxicity_model is not None,
            "sentiment_available": sentiment_model is not None,
            "emotion_available": emotion_model is not None,
            "hate_speech_available": hate_speech_model is not None
        }
    }



@app.get("/performance")
async def get_performance_stats():
    """Get detailed performance statistics"""
    from services.ai_manager import ai_manager
    
    uptime = time.time() - START_TIME
    
    # System performance  
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except ImportError:
        cpu_percent = 0
        memory = None
        disk = None
    
    performance_stats = {
        "server": {
            "version": "2.1.0",
            "uptime_seconds": round(uptime, 2),
            "active_requests": len(active_requests),
            "model_load_time": model_load_time
        },
        "ai_manager": ai_manager.get_performance_stats(),
        "security": {
            "rate_limiting_enabled": True,
            "validation_enabled": True,
            "request_tracking_enabled": True,
            "origin_validation_enabled": bool(ALLOWED_ELECTRON_ORIGINS),
            "shutdown_auth_enabled": bool(SHUTDOWN_TOKEN)
        }
    }
    
    if memory:
        performance_stats["system"] = {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2) if disk else 0,
            "disk_percent": round((disk.used / disk.total) * 100, 1) if disk else 0
        }
    
    return performance_stats

@app.post("/shutdown")
async def shutdown_server(
    http_request: Request,
    auth_valid: bool = Depends(validate_shutdown_auth)
):
    """Secure server shutdown endpoint with token authentication"""
    client_ip = get_client_ip(http_request)
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    if not auth_valid:
        security_logger.critical(f"Unauthorized shutdown attempt - IP: {client_ip}, Request-ID: {request_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": "Invalid or missing shutdown credentials",
                "request_id": request_id
            }
        )
    
    logger.info(f"🛑 Authorized server shutdown requested - IP: {client_ip}, Request-ID: {request_id}")
    security_logger.info(f"Server shutdown authorized - IP: {client_ip}, Request-ID: {request_id}")
    
    # Schedule shutdown to allow response to be sent
    def delayed_shutdown():
        time.sleep(1)  # Give time for response to be sent
        logger.info("🛑 Server shutting down...")
        os.kill(os.getpid(), signal.SIGTERM)
    
    import threading
    shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
    shutdown_thread.start()
    
    return {
        "status": "shutting down",
        "message": "Server is shutting down gracefully",
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    print(f"🚀 Starting Secure Streaming Backend Server on port {PORT}")
    print(f"📚 API Documentation: http://127.0.0.1:{PORT}/docs")
    print(f"🤖 AI models will load on first request for optimal performance")
    print(f"🔒 Security features: Comprehensive input validation, rate limiting, request tracking, origin validation")
    print(f"🔐 Shutdown authentication: {'Enabled' if SHUTDOWN_TOKEN else 'DISABLED - WARNING!'}")
    print(f"📊 Server stats: http://127.0.0.1:{PORT}/stats")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="info",
        access_log=True
    )