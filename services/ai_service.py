import os
import google.generativeai as genai
from config import Config
from utils.logger import setup_logger
from pathlib import Path

logger = setup_logger('ai_service')

class AIService:
    """Service for AI-powered meter reading verification using Gemini"""
    
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Use Gemini 2.0 Flash (Experimental) or fallback to 1.5 Flash
            self.model_name = 'gemini-2.0-flash-exp' 
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"AIService initialized with model: {self.model_name}")
        else:
            logger.warning("GEMINI_API_KEY not found. AI features will be disabled.")
            self.model = None

    def verify_reading(self, image_path: str, claimed_value: float) -> dict:
        """
        Verify if the claimed reading matches the meter photo.
        
        Args:
            image_path: Path to the meter image file
            claimed_value: The reading value submitted by the engineer
            
        Returns:
            dict: Verification result containing match status, extracted value, and reasoning
        """
        if not self.model:
            return {
                "error": "AI service not configured",
                "match": False,
                "confidence": 0.0
            }
            
        try:
            # Validate image path
            path = Path(image_path)
            if not path.exists():
                return {
                    "error": f"Image file not found: {image_path}",
                    "match": False
                }
                
            # Upload/Load image
            # For local files, we can pass the bytes or path directly to some Gemini SDKs,
            # but usually we use the file API or PIL. Let's use PIL for simplicity.
            import PIL.Image
            img = PIL.Image.open(path)
            
            prompt = f"""
            You are an expert meter reading verifier. 
            Analyze this electricity meter image.
            
            Task:
            1. Extract the numeric reading visible on the display. Ignore decimal places if they are small/insignificant, but note them.
            2. Compare it with the claimed value: {claimed_value}
            3. Determine if they match (allow for minor differences like decimal rounding or last digit ambiguity).
            
            Return a JSON object with this structure:
            {{
                "extracted_value": <number or null>,
                "match": <boolean>,
                "reasoning": "<short explanation>",
                "confidence": <float between 0 and 1>
            }}
            """
            
            response = self.model.generate_content([prompt, img])
            
            # Parse JSON from response
            import json
            import re
            
            text = response.text
            # Extract JSON block if present
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_str = match.group(0)
                result = json.loads(json_str)
                return result
            else:
                logger.warning(f"Could not parse JSON from AI response: {text}")
                return {
                    "error": "Failed to parse AI response",
                    "raw_response": text,
                    "match": False
                }
                
        except Exception as e:
            logger.error(f"Error verifying reading: {e}")
            return {
                "error": str(e),
                "match": False
            }
