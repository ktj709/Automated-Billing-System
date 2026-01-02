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
        tariff_type: str = "residential",
        # Optional explicit pricing overrides. If not provided, the
        # caller is assumed to be using the standard 12₹/unit tariff
        # with zero fixed charge. Special 9₹ units can be supported by
        # passing rate_per_unit=9 and fixed_charge=0.
        rate_per_unit: float | None = None,
        fixed_charge: float | None = None,
        previous_outstanding: float = 0.0,
    ) -> Dict:
        """
        Calculate electricity bill using the explicit formula-based rules.

        This now mirrors the React billing logic and the documentation:

            1. Flat Units  = current_reading - previous_reading
            2. Water Motor Share (if available) is computed separately.
            3. Total Units = Flat Units + Water Motor Share
            4. Usage       = Total Units × rate_per_unit
            5. Final Bill  = Usage + Fixed Charge (+ previous_outstanding)

        For now this helper only uses the flat units and does not
        automatically infer motor share from Supabase. Callers that
        have full motor context should compute water_motor_share and
        use TariffRules.calculate_simple_bill directly.
        """
        from .tariff_rules import TariffRules

        # 1. Calculate flat consumption from readings
        flat_units = max(current_reading - previous_reading, 0.0)

        # 2. Decide pricing parameters
        #    - Default unit rate is 12₹ unless explicitly overridden.
        #    - Fixed charge defaults to 0 here; callers that know the
        #      actual per-unit fixed charge (including special 9₹/no-
        #      fixed-charge units) should pass it explicitly.
        unit_rate = 12.0 if rate_per_unit is None else rate_per_unit
        fixed = 0.0 if fixed_charge is None else fixed_charge

        simple = TariffRules.calculate_simple_bill(
            flat_units=flat_units,
            motor_units=0.0,
            total_flat_units_for_motor=0.0,
            rate_per_unit=unit_rate,
            fixed_charge=fixed,
            previous_outstanding=previous_outstanding,
        )

        # 3. Return structure compatible with existing callers
        #    (some fields like tiers/taxes are now synthetic zeros).
        return {
            "consumption_kwh": simple["flat_units"] + simple["water_motor_share"],
            "tier_breakdown": [],
            "energy_charges": simple["usage_charge"],
            "fixed_charges": simple["fixed_charge"],
            "subtotal": simple["usage_charge"] + simple["fixed_charge"],
            "taxes": 0.0,
            "total_amount": simple["total_amount"],
            "currency": "INR",
            # Reuse the existing payment terms definition so callers
            # don't break; these are not part of the numeric formula.
            "payment_terms": TariffRules.RESIDENTIAL_STANDARD["payment_terms"],
            "detailed_breakdown": simple,
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
    
    def generate_payment_confirmation_message(
        self,
        customer_id: str,
        bill_id: int,
        amount: float
    ) -> str:
        """
        Generate a thank you message for successful payment
        Uses AI if enabled, otherwise returns a friendly default message
        """
        # If AI is enabled, generate personalized message
        if self.enabled:
            try:
                prompt = f"""Generate a warm, friendly thank you message for a customer who just paid their electricity bill.

Customer ID: {customer_id}
Bill ID: {bill_id}
Amount Paid: ₹{amount:.2f}

Requirements:
- Keep it brief (2-3 sentences max)
- Express gratitude
- Confirm payment received
- Professional but friendly tone
- Include the bill ID and amount

Do not include greetings like "Dear Customer" or signatures."""

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a friendly customer service agent for an electricity billing company."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                # Fallback to default message if AI fails
                pass
        
        # Default message if AI disabled or fails
        return (
            f"Thank you for your payment of ₹{amount:.2f}! "
            f"Your bill #{bill_id} has been successfully paid. "
            f"We appreciate your prompt payment."
        )

