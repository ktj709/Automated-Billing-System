import requests
from typing import Dict
from config import Config
from datetime import datetime
from utils.retry_decorator import retry, CircuitBreaker
from utils.logger import setup_logger

logger = setup_logger('whatsapp_service')


class WhatsAppService:
    """WhatsApp Business API service for sending notifications"""
    
    def __init__(self):
        self.phone_number_id = Config.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = Config.WHATSAPP_ACCESS_TOKEN
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        # Check if WhatsApp is properly configured
        self.enabled = (
            self.phone_number_id and 
            self.access_token and 
            'your_' not in self.phone_number_id and
            'your_' not in self.access_token
        )
        
        if self.enabled:
            logger.info("WhatsApp service enabled")
        else:
            logger.warning("WhatsApp service in mock mode - not configured")
        
        # Circuit breaker for WhatsApp API calls
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
    
    @retry(max_attempts=3, delay=2, backoff=2, exceptions=(requests.exceptions.RequestException,))
    def send_message(self, to_phone: str, message: str) -> Dict:
        """
        Send a WhatsApp message to a customer
        
        Args:
            to_phone: Customer's phone number (international format)
            message: Message text to send
        
        Returns:
            Dict with message ID and status
        """
        logger.debug(f"Sending WhatsApp message to {to_phone}")
        
        # Mock mode if not configured
        if not self.enabled:
            logger.info(f"Mock WhatsApp to {to_phone}: {message[:50]}...")
            print(f"\n📱 MOCK WhatsApp Message")
            print(f"To: {to_phone}")
            print(f"Message: {message}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return {
                "message_id": f"mock_msg_{int(datetime.now().timestamp())}",
                "status": "sent_mock",
                "success": True,
                "mock": True
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Clean phone number - remove '+' and any spaces
        clean_phone = to_phone.replace('+', '').replace(' ', '').replace('-', '')
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            
            logger.info(f"WhatsApp message sent successfully: {message_id}")
            return {
                "message_id": message_id,
                "status": "sent",
                "success": True,
                "mock": False
            }
        
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            # Try to extract API error response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = f"{e} - API Response: {error_data}"
                except:
                    error_detail = f"{e} - Status: {e.response.status_code}, Text: {e.response.text[:200]}"
            
            logger.error(f"WhatsApp API error: {error_detail}")
            return {
                "message_id": None,
                "status": "failed",
                "success": False,
                "error": error_detail,
                "mock": False
            }
    
    def send_notification(self, phone_number: str, message: str) -> Dict:
        """
        Alias for send_message for compatibility
        """
        return self.send_message(phone_number, message)
    
    @retry(max_attempts=3, delay=2, backoff=2, exceptions=(requests.exceptions.RequestException,))
    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "en",
        parameters: list = None
    ) -> Dict:
        """
        Send a WhatsApp template message
        
        Args:
            to_phone: Customer's phone number
            template_name: Name of approved template
            language_code: Language code (default: en)
            parameters: List of parameter values for template
        
        Returns:
            Dict with message ID and status
        """
        logger.debug(f"Sending WhatsApp template '{template_name}' to {to_phone}")
        
        if not self.enabled:
            logger.warning("WhatsApp not configured - cannot send template message")
            return {
                "message_id": None,
                "status": "failed",
                "success": False,
                "error": "WhatsApp not configured",
                "mock": True
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        components = []
        if parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            
            logger.info(f"WhatsApp template message sent successfully: {message_id}")
            return {
                "message_id": message_id,
                "status": "sent",
                "success": True
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp template API error: {e}")
            return {
                "message_id": None,
                "status": "failed",
                "success": False,
                "error": str(e)
            }
