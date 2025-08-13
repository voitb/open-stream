from typing import Dict, Any
from .ai_manager import ai_manager
import logging

logger = logging.getLogger(__name__)

class SentimentService:
    """Service for sentiment and emotion analysis"""
    
    def __init__(self):
        self.sentiment_model = None
        self.emotion_model = None
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment (1-5 stars)"""
        if not self.sentiment_model:
            self.sentiment_model = ai_manager.get_sentiment_model()
        
        try:
            results = self.sentiment_model(text)
            
            # Parse star rating (model zwraca 1-5 stars)
            result = results[0]
            stars = int(result['label'].split()[0])  # "5 stars" -> 5
            
            # Convert to sentiment
            if stars >= 4:
                sentiment = "positive"
            elif stars <= 2:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "stars": stars,
                "confidence": result['score']
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "stars": 3,
                "confidence": 0,
                "error": str(e)
            }
    
    async def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """Detect emotions in text"""
        if not self.emotion_model:
            self.emotion_model = ai_manager.get_emotion_model()
        
        try:
            results = self.emotion_model(text)
            
            # Get all emotions with scores
            emotions = {r['label']: r['score'] for r in results}
            
            # Get dominant emotion
            dominant = max(results, key=lambda x: x['score'])
            
            return {
                "dominant_emotion": dominant['label'],
                "confidence": dominant['score'],
                "all_emotions": emotions
            }
            
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return {
                "dominant_emotion": "neutral",
                "confidence": 0,
                "error": str(e)
            }

sentiment_service = SentimentService()