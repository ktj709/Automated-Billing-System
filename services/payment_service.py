from typing import Dict
from config import Config
from utils.retry_decorator import retry, CircuitBreaker
from utils.logger import setup_logger

logger = setup_logger('payment_service')

# Import stripe only if available (optional)
try:
    import stripe
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False
    logger.warning("Stripe not installed - payment service in mock mode")


class PaymentService:
    """Stripe payment service for generating payment links"""
    
    def __init__(self):
        # Only enable if we have a real Stripe key (not placeholder)
        has_real_key = (
            HAS_STRIPE and 
            Config.STRIPE_API_KEY and 
            Config.STRIPE_API_KEY.startswith('sk_test_') and
            len(Config.STRIPE_API_KEY) > 20 and
            'your-api-key' not in Config.STRIPE_API_KEY
        )
        
        if has_real_key:
            stripe.api_key = Config.STRIPE_API_KEY
            self.enabled = True
            logger.info("Payment service enabled with Stripe")
        else:
            self.enabled = False
            logger.warning("Payment service in mock mode - Stripe not configured")
        
        # Circuit breaker for Stripe API calls
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def create_payment_link(
        self,
        amount: float,
        meter_id: str = None,
        bill_id: int = None,
        customer_id: str = None,
        description: str = None,
        currency: str = "inr",
        **kwargs
    ) -> Dict:
        """
        Create a Stripe payment link for a bill
        
        Args:
            amount: Amount in INR (Indian Rupees) or specified currency
            meter_id: Meter identifier
            bill_id: Bill identifier
            customer_id: Customer identifier
            description: Optional description
            currency: Currency code (default: inr)
            **kwargs: Additional metadata
        
        Returns:
            Dict with payment link URL and ID
        """
        logger.debug(f"Creating payment link for ₹{amount} (bill_id={bill_id})")
        
        if not self.enabled:
            # Return mock payment link if Stripe not configured
            logger.info(f"Returning mock payment link for bill {bill_id}")
            return {
                "url": f"http://localhost:5000/mock-payment/{bill_id or 'test'}",
                "id": f"mock_link_{bill_id or 'test'}",
                "active": True
            }
        
        try:
            # Convert amount to smallest currency unit (paise for INR, cents for USD)
            amount_smallest = int(amount * 100)
            
            # Prepare metadata - include all necessary info for webhook
            metadata = {
                "bill_id": str(bill_id) if bill_id else "N/A",
                "customer_id": customer_id or "N/A",
                "meter_id": meter_id or "N/A"
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Create a price
            logger.debug(f"Creating Stripe price: {amount_smallest} {currency}")
            price = stripe.Price.create(
                currency=currency.lower(),
                unit_amount=amount_smallest,
                product_data={
                    "name": description or f"Electricity Bill - {meter_id or 'N/A'}"
                }
            )
            
            # Create payment link
            logger.debug(f"Creating Stripe payment link with price {price.id}")
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    "price": price.id,
                    "quantity": 1
                }],
                metadata=metadata
            )
            
            # Add payment_link_id to metadata for tracking
            metadata['payment_link_id'] = payment_link.id
            
            logger.info(f"Created payment link {payment_link.id} for bill {bill_id}")
            return {
                "url": payment_link.url,
                "id": payment_link.id,
                "active": payment_link.active
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment link: {e}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating payment link: {e}")
            raise
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def retrieve_payment_link(self, payment_link_id: str) -> Dict:
        """Retrieve payment link details"""
        logger.debug(f"Retrieving payment link {payment_link_id}")
        
        if not self.enabled:
            logger.info(f"Returning mock payment link details for {payment_link_id}")
            return {
                "url": f"http://localhost:5000/mock-payment/{payment_link_id}",
                "id": payment_link_id,
                "active": True
            }
        
        try:
            payment_link = stripe.PaymentLink.retrieve(payment_link_id)
            logger.info(f"Retrieved payment link {payment_link_id}")
            return {
                "url": payment_link.url,
                "id": payment_link.id,
                "active": payment_link.active
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment link: {e}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving payment link: {e}")
            raise
