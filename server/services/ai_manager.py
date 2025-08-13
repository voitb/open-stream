import os
import time
import psutil
import asyncio
import hashlib
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from collections import OrderedDict
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import logging

logger = logging.getLogger(__name__)

class ModelLoadingStatus:
    """Track model loading status for progressive loading"""
    UNLOADED = "unloaded"
    LOADING = "loading" 
    LOADED = "loaded"
    ERROR = "error"

class MemoryManager:
    """Simple memory tracker - no longer manages unloading"""
    
    def __init__(self, max_memory_gb: float = 10.0):
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.model_usage_order = OrderedDict()
        self.model_memory_usage = {}
        
    def record_model_usage(self, model_name: str):
        """Record that a model was used (for monitoring only)"""
        self.model_usage_order[model_name] = time.time()
    
    def get_current_memory_usage(self) -> int:
        """Get current process memory usage in bytes"""
        return psutil.Process().memory_info().rss
    
    def should_cleanup_memory(self) -> bool:
        """Memory cleanup is disabled - always returns False"""
        return False
    
    def get_models_to_unload(self, available_models: List[str]) -> List[str]:
        """Model unloading is disabled - always returns empty list"""
        return []

class AnalysisCache:
    """Cache for analysis results to avoid reprocessing identical requests"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, text: str, model_type: str, options: Dict[str, Any] = None) -> str:
        """Generate cache key for text and analysis options"""
        content = f"{text}:{model_type}:{options or {}}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, model_type: str, options: Dict[str, Any] = None) -> Optional[Any]:
        """Get cached result if available and not expired"""
        key = self._generate_key(text, model_type, options)
        
        if key in self.cache:
            access_time = self.access_times.get(key, 0)
            if time.time() - access_time < self.ttl_seconds:
                # Move to end (most recently used)
                result = self.cache[key]
                del self.cache[key]
                self.cache[key] = result
                self.access_times[key] = time.time()
                return result
            else:
                # Expired, remove
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def set(self, text: str, model_type: str, result: Any, options: Dict[str, Any] = None):
        """Cache analysis result"""
        key = self._generate_key(text, model_type, options)
        
        # Remove oldest entries if at capacity
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = result
        self.access_times[key] = time.time()

class OptimizedAIManager:
    """High-performance AI manager with progressive loading, memory management, and caching"""
    
    def __init__(self):
        # Set optimal cache directory
        self.models_dir = self._get_optimal_cache_dir()
        self.models_dir.mkdir(exist_ok=True)
        
        # Configure Hugging Face environment
        os.environ['TRANSFORMERS_CACHE'] = str(self.models_dir)
        os.environ['HF_HOME'] = str(self.models_dir)
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Avoid warnings
        
        # Optimize PyTorch for CPU inference
        self._configure_pytorch()
        
        # Model management
        self.models = {}
        self.model_status = {}
        self.model_loading_locks = {}
        
        # Performance optimizations
        self.memory_manager = MemoryManager(max_memory_gb=10.0)
        self.analysis_cache = AnalysisCache()
        
        # Model priority for loading (toxicity first for safety)
        self.model_priority = ['toxicity', 'sentiment', 'emotion', 'hate_speech']
        
        # Load all models synchronously at startup
        self._load_all_models_sync()
        
        logger.info(f"✅ AI Manager initialized - all models loaded and kept in memory")
        logger.info(f"📁 Models cache: {self.models_dir}")
        logger.info(f"🧠 Memory limit: {self.memory_manager.max_memory_bytes / (1024**3):.1f}GB (no auto-unloading)")
        logger.info(f"⚡ Cache size: {self.analysis_cache.max_size} entries")
        logger.info(f"🚀 Models loaded: {list(self.models.keys())}")
    
    def _get_optimal_cache_dir(self) -> Path:
        """Choose fastest available storage for model cache"""
        base_dir = Path(__file__).parent.parent / "models"
        
        # Try to detect if we're on SSD by checking common SSD paths
        potential_ssd_paths = [
            Path.home() / ".cache" / "open-stream-models",
            Path("/tmp") / "open-stream-models" if os.name != 'nt' else None,
        ]
        
        # Filter out None values and check which paths exist or can be created
        for path in filter(None, potential_ssd_paths):
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Simple write test to ensure we have permissions
                test_file = path / "test_write"
                test_file.write_text("test")
                test_file.unlink()
                return path
            except (PermissionError, OSError):
                continue
        
        return base_dir
    
    def _configure_pytorch(self):
        """Configure PyTorch for optimal CPU inference"""
        # CPU optimization
        cpu_count = os.cpu_count() or 4
        torch.set_num_threads(min(4, cpu_count))  # Use up to 4 threads
        torch.set_num_interop_threads(2)
        
        # Enable optimizations if available
        try:
            torch.backends.mkldnn.enabled = True
        except AttributeError:
            pass
        
        # Set optimal device
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"🖥️ Using device: {'GPU' if self.device == 0 else 'CPU'}")
        logger.info(f"🧵 PyTorch threads: {torch.get_num_threads()}")
    
    def _load_all_models_sync(self):
        """Load all models synchronously at startup"""
        logger.info("🚀 Loading all models synchronously...")
        
        for model_type in self.model_priority:
            try:
                logger.info(f"📥 Loading {model_type} model...")
                self._load_model_directly(model_type)
                logger.info(f"✅ {model_type.title()} model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load {model_type} model: {e}")
                self.model_status[model_type] = ModelLoadingStatus.ERROR
        
        logger.info("✅ All models loaded synchronously")
    
    def _load_model_directly(self, model_type: str):
        """Load a model directly without memory checks or threading"""
        model = self._load_model_by_type(model_type)
        self.models[model_type] = model
        self.model_status[model_type] = ModelLoadingStatus.LOADED
        self.memory_manager.record_model_usage(model_type)
    
    def _ensure_model_loaded(self, model_type: str, background: bool = False) -> bool:
        """Ensure a model is loaded - simplified without memory management"""
        if model_type in self.models:
            self.memory_manager.record_model_usage(model_type)
            return True
        
        # If model not loaded and we're past startup, try to load it
        logger.warning(f"Model {model_type} not loaded at startup, loading now...")
        try:
            self._load_model_directly(model_type)
            logger.info(f"✅ {model_type.title()} model loaded successfully")
            return True
        except Exception as e:
            self.model_status[model_type] = ModelLoadingStatus.ERROR
            logger.error(f"❌ Failed to load {model_type} model: {e}")
            return False
    
    def _load_model_by_type(self, model_type: str):
        """Load specific model type with ultra-simple configuration"""
        model_configs = {
            'toxicity': {
                'task': 'text-classification',
                'model': 'unitary/toxic-bert',
                'max_length': 512
            },
            'sentiment': {
                'task': 'sentiment-analysis', 
                'model': 'distilbert-base-uncased-finetuned-sst-2-english',
                'max_length': 256
            },
            'emotion': {
                'task': 'text-classification',
                'model': 'j-hartmann/emotion-english-distilroberta-base',
                'max_length': 256
            },
            'hate_speech': {
                'task': 'text-classification',
                'model': 'Hate-speech-CNERG/dehatebert-mono-english',
                'max_length': 512
            }
        }
        
        config = model_configs.get(model_type)
        if not config:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Ultra-simple configuration - only essential parameters
        # Let transformers handle all tokenizer configuration automatically
        logger.debug(f"Creating pipeline for {model_type} with minimal configuration")
        return pipeline(
            config['task'],
            model=config['model'],
            device=self.device,
            max_length=config['max_length'],
            truncation=True,
            batch_size=1,
        )
    
    
    def analyze_with_caching(self, text: str, model_type: str, options: Dict[str, Any] = None) -> Any:
        """Analyze text with result caching"""
        # Check cache first
        cached_result = self.analysis_cache.get(text, model_type, options)
        if cached_result is not None:
            return cached_result
        
        # Ensure model is loaded
        if not self._ensure_model_loaded(model_type):
            raise RuntimeError(f"Failed to load {model_type} model")
        
        # Perform analysis
        model = self.models[model_type]
        result = model(text)
        
        # Cache result
        self.analysis_cache.set(text, model_type, result, options)
        
        return result
    
    def get_toxicity_model(self):
        """Get or load toxicity detection model"""
        if not self._ensure_model_loaded('toxicity'):
            raise RuntimeError("Failed to load toxicity model")
        return self.models['toxicity']
    
    def get_sentiment_model(self):
        """Get or load sentiment analysis model"""
        if not self._ensure_model_loaded('sentiment'):
            raise RuntimeError("Failed to load sentiment model")
        return self.models['sentiment']
    
    def get_emotion_model(self):
        """Get or load emotion detection model"""
        if not self._ensure_model_loaded('emotion'):
            raise RuntimeError("Failed to load emotion model")
        return self.models['emotion']
    
    def get_hate_speech_model(self):
        """Get or load hate speech detection model"""
        if not self._ensure_model_loaded('hate_speech'):
            raise RuntimeError("Failed to load hate speech model")
        return self.models['hate_speech']
    
    def analyze_toxicity(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """Analyze toxicity with caching support"""
        if use_cache:
            return self.analyze_with_caching(text, 'toxicity')
        else:
            model = self.get_toxicity_model()
            return model(text)
    
    def analyze_sentiment(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """Analyze sentiment with caching support"""
        if use_cache:
            return self.analyze_with_caching(text, 'sentiment')
        else:
            model = self.get_sentiment_model()
            return model(text)
    
    def get_model_status(self) -> Dict[str, str]:
        """Get current status of all models"""
        status = {}
        for model_type in self.model_priority:
            if model_type in self.models:
                status[model_type] = ModelLoadingStatus.LOADED
            elif model_type in self.model_status:
                status[model_type] = self.model_status[model_type]
            else:
                status[model_type] = ModelLoadingStatus.UNLOADED
        return status
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance and memory statistics"""
        memory_info = psutil.Process().memory_info()
        
        return {
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 1),
            "memory_limit_mb": round(self.memory_manager.max_memory_bytes / 1024 / 1024, 1),
            "memory_management": "disabled",
            "models_loaded": len(self.models),
            "models_status": self.get_model_status(),
            "cache_size": len(self.analysis_cache.cache),
            "cache_hit_rate": getattr(self.analysis_cache, '_hit_rate', 0.0),
            "loading_strategy": "synchronous_startup"
        }
    
    def preload_models(self, model_types: List[str] = None):
        """All models are already loaded at startup - this method is now a no-op"""
        logger.info("All models are already loaded at startup - no action needed")

# Singleton instance
ai_manager = OptimizedAIManager()
