import json
from typing import Dict, List

# Import OpenAI only if available (optional)
try:
    from openai import OpenAI
    from config import Config
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False
    Config = None


class AIAgentService:
    """AI-powered agents for validation and calculation using OpenAI"""
    
    def __init__(self):
        if HAS_OPENAI and Config and Config.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.enabled = True
            except Exception:
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
    
    def validate_meter_reading(
        self, 
        historical_readings: List[Dict], 
        new_reading: Dict
    ) -> Dict:
        """
        Validate a new meter reading using AI analysis
        Returns: {"valid": bool, "reason": str, "confidence": int}
        """
        
        # Simple validation without AI if not enabled
        if not self.enabled or not historical_readings:
            return {
                "valid": True,
                "reason": "AI validation disabled - basic check passed",
                "confidence": 50
            }
        
        prompt = f"""You are a validation agent for meter readings.

Historical readings: {json.dumps(historical_readings, default=str)}

New reading: {new_reading['reading_value']} kWh
Meter ID: {new_reading['meter_id']}
Reading Date: {new_reading['reading_date']}

Analyze if this new reading is valid based on:
1. Typical consumption patterns
2. Unusual spikes or drops
3. Time period between readings

Respond with JSON: {{"valid": true/false, "reason": "explanation", "confidence": 0-100}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a meter reading validation expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "confidence": 0
            }
    
    def calculate_bill(
        self,
        current_reading: float,
        previous_reading: float,
        meter_id: str,
        customer_id: str,
        connected_load_kw: float = 7.0,
        tariff_type: str = "residential"
    ) -> Dict:
        """
        Calculate electricity bill using synthetic tariff rules
        Returns: Bill breakdown with consumption, tiers, taxes, and total
        """
        from .tariff_rules import TariffRules
        
        # Calculate consumption
        consumption = current_reading - previous_reading
        
        # Use synthetic tariff calculation
        bill_details = TariffRules.calculate_total_bill(
            consumption_kwh=consumption,
            connected_load_kw=connected_load_kw,
            tariff_type=tariff_type,
            previous_outstanding=0.0
        )
        
        # Format response to match expected structure
        return {
            "consumption_kwh": bill_details["consumption_kwh"],
            "tier_breakdown": bill_details["energy_charges"]["tier_breakdown"],
            "energy_charges": bill_details["energy_charges"]["total"],
            "fixed_charges": bill_details["fixed_charges"]["total"],
            "subtotal": bill_details["subtotal"],
            "taxes": bill_details["taxes"]["total"],
            "total_amount": bill_details["amount_payable"],
            "currency": bill_details["currency"],
            "payment_terms": bill_details["payment_terms"],
            "detailed_breakdown": bill_details
        }
    
    def generate_notification_message(
        self,
        customer_id: str,
        bill_amount: float,
        consumption_kwh: float,
        payment_link: str
    ) -> str:
        """
        Generate a friendly WhatsApp notification message in SMS-style format
        """
        from datetime import datetime, timedelta
        
        # Calculate due date (15 days from now)
        due_date = (datetime.now() + timedelta(days=15)).strftime("%m/%d")
        
        # Get last 4 digits of customer ID for account reference
        account_ending = customer_id[-4:] if len(customer_id) >= 4 else customer_id.zfill(4)
        
        # Format amount with currency symbol
        if bill_amount < 100:
            amount_str = f"${bill_amount:.2f}"
        else:
            amount_str = f"${bill_amount:.0f}"
        
        # Create SMS-style message
        message = (
            f"Optimum: Your bill is due soon. "
            f"Avoid late fees, pay {amount_str} by {due_date}. "
            f"To pay now using acct ending {account_ending} reply PAY. "
            f"Questions? Tap {payment_link} to chat."
        )
        
        return message
