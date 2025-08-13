from typing import Dict, List, Any
from .ai_manager import ai_manager
import logging

logger = logging.getLogger(__name__)

class ToxicityService:
    """Service for detecting toxic content"""
    
    def __init__(self):
        self.model = None
    
    def _ensure_model(self):
        """Lazy load model"""
        if not self.model:
            self.model = ai_manager.get_toxicity_model()
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for toxicity"""
        self._ensure_model()
        
        try:
            # Run model
            results = self.model(text)
            
            # Parse results
            toxic_score = 0
            toxic_label = None
            
            for result in results:
                if 'TOXIC' in result['label'].upper():
                    toxic_score = result['score']
                    toxic_label = result['label']
                    break
            
            # Determine severity
            severity = self._get_severity(toxic_score)
            
            return {
                "toxic": toxic_score > 0.5,
                "score": toxic_score,
                "severity": severity,
                "label": toxic_label,
                "action": self._suggest_action(toxic_score)
            }
            
        except Exception as e:
            logger.error(f"Toxicity analysis failed: {e}")
            return {
                "toxic": False,
                "score": 0,
                "severity": "unknown",
                "error": str(e)
            }
    
    def _get_severity(self, score: float) -> str:
        if score < 0.3:
            return "none"
        elif score < 0.5:
            return "low"
        elif score < 0.7:
            return "medium"
        elif score < 0.9:
            return "high"
        else:
            return "extreme"
    
    def _suggest_action(self, score: float) -> str:
        if score < 0.5:
            return "allow"
        elif score < 0.7:
            return "warning"
        elif score < 0.85:
            return "timeout"
        else:
            return "ban"

toxicity_service = ToxicityService()