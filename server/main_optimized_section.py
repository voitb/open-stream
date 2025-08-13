# Updated sections for main.py to use optimized AI manager

# Replace the load_models function:
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


# Updated analyze_text_with_ai function:
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


# Add new performance stats endpoint:
@app.get("/performance")
async def get_performance_stats():
    """Get detailed performance statistics"""
    from services.ai_manager import ai_manager
    
    uptime = time.time() - START_TIME
    
    # System performance
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "server": {
            "version": "2.1.0",
            "uptime_seconds": round(uptime, 2),
            "active_requests": len(active_requests),
            "model_load_time": model_load_time
        },
        "ai_manager": ai_manager.get_performance_stats(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1)
        },
        "security": {
            "rate_limiting_enabled": True,
            "validation_enabled": True,
            "request_tracking_enabled": True,
            "origin_validation_enabled": bool(ALLOWED_ELECTRON_ORIGINS),
            "shutdown_auth_enabled": bool(SHUTDOWN_TOKEN)
        }
    }
