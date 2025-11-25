from flask import Flask, request, jsonify
from datetime import datetime
import json
import atexit
from config import Config
from services import (
    DatabaseService,
    Neo4jService,
    AIAgentService,
    PaymentService,
    WhatsAppService,
    AuthService,
    get_scheduler
)
from utils.retry_decorator import handle_api_errors
from utils.logger import setup_logger, LogContext

# Setup logging
logger = setup_logger('billing_app')

app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
logger.info("Initializing services...")
db_service = DatabaseService()
neo4j_service = Neo4jService()
ai_service = AIAgentService()
payment_service = PaymentService()
whatsapp_service = WhatsAppService()
auth_service = AuthService()

# Initialize scheduler
scheduler = get_scheduler()
scheduler.start()
logger.info("Billing scheduler started")

# Ensure scheduler stops on app shutdown
def shutdown_scheduler():
    logger.info("Shutting down scheduler...")
    scheduler.stop()

atexit.register(shutdown_scheduler)

logger.info("All services initialized successfully")


@app.route('/webhook/meter-reading', methods=['POST'])
@handle_api_errors
def process_meter_reading():
    """
    Main webhook endpoint for processing meter readings and generating bills
    
    Expected JSON payload:
    {
        "user_id": "auth0_user_id",
        "meter_id": "meter_123",
        "customer_id": "cust_456",
        "customer_phone": "+1234567890",
        "reading_value": 1250.5,
        "reading_date": "2025-11-18"
    }
    """
    
    with LogContext(logger, "Process meter reading webhook"):
        # Step 1: Verify authentication
        logger.info("Step 1: Verifying authentication")
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Missing authorization header")
            return jsonify({"error": "Missing authorization header"}), 401
        
        # Check header auth token
        token = auth_header.replace('Bearer ', '')
        if not auth_service.verify_header_auth(token):
            # Try Auth0 verification
            user_info = auth_service.verify_token(token)
            if not user_info or user_info.get('sub') != request.json.get('user_id'):
                logger.warning("Invalid authentication token")
                return jsonify({"error": "Invalid authentication"}), 401
        
        # Step 2: Extract request data
        logger.info("Step 2: Extracting request data")
        data = request.json
        meter_id = data.get('meter_id')
        customer_id = data.get('customer_id')
        customer_phone = data.get('customer_phone')
        reading_value = data.get('reading_value')
        reading_date = data.get('reading_date')
        
        # Validate required fields
        if not all([meter_id, customer_id, reading_value, reading_date]):
            logger.warning("Missing required fields in request")
            return jsonify({"error": "Missing required fields"}), 400
        
        # Step 3: Get historical readings
        logger.info(f"Step 3: Fetching historical readings for meter {meter_id}")
        historical_readings = db_service.get_historical_readings(meter_id, limit=10)
        
        if not historical_readings:
            logger.warning(f"No historical data found for meter {meter_id}")
            return jsonify({"error": "No historical data found for meter"}), 404
        
        # Step 4: Validate meter reading using AI
        logger.info("Step 4: Validating meter reading with AI")
        validation_result = ai_service.validate_meter_reading(
            historical_readings=historical_readings,
            new_reading={
                "meter_id": meter_id,
                "reading_value": reading_value,
                "reading_date": reading_date
            }
        )
        
        if not validation_result.get('valid'):
            logger.warning(f"Invalid meter reading: {validation_result.get('reason')}")
            return jsonify({
                "error": "Invalid meter reading",
                "reason": validation_result.get('reason'),
                "confidence": validation_result.get('confidence')
            }), 422
        
        # Step 5: Calculate bill using synthetic tariff rules
        previous_reading = historical_readings[0]['reading_value']
        connected_load = data.get('connected_load_kw', 7.0)  # Default 7KW
        tariff_type = data.get('tariff_type', 'residential')
        
        bill_calculation = ai_service.calculate_bill(
            current_reading=reading_value,
            previous_reading=previous_reading,
            meter_id=meter_id,
            customer_id=customer_id,
            connected_load_kw=connected_load,
            tariff_type=tariff_type
        )
        
        # Step 6: Store bill in database
        bill_data = {
            "customer_id": customer_id,
            "meter_id": meter_id,
            "billing_period_start": historical_readings[0]['reading_date'],
            "billing_period_end": reading_date,
            "consumption_kwh": bill_calculation['consumption_kwh'],
            "amount": bill_calculation['total_amount'],
            "status": "pending",
            "created_at": datetime.now()
        }
        
        created_bill = db_service.create_bill(bill_data)
        bill_id = created_bill['id']
        
        # Step 7: Save bill relationship in Neo4j (optional)
        try:
            neo4j_service.create_bill_relationship({
                "customer_id": customer_id,
                "meter_id": meter_id,
                "bill_id": bill_id,
                "amount": bill_calculation['total_amount'],
                "consumption": bill_calculation['consumption_kwh'],
                "date": datetime.now().isoformat()
            })
        except Exception as e:
            # Neo4j is optional, continue if it fails
            print(f"Neo4j relationship creation failed: {e}")
        
        # Step 8: Create payment link with Stripe
        payment_link = payment_service.create_payment_link(
            amount=bill_calculation['total_amount'],
            meter_id=meter_id,
            bill_id=bill_id,
            customer_id=customer_id
        )
        
        # Step 9: Update bill with payment link
        db_service.update_bill_payment_info(
            bill_id=bill_id,
            payment_link=payment_link['url'],
            payment_link_id=payment_link['id']
        )
        
        # Step 10: Generate notification message using AI
        notification_message = ai_service.generate_notification_message(
            customer_id=customer_id,
            bill_amount=bill_calculation['total_amount'],
            consumption_kwh=bill_calculation['consumption_kwh'],
            payment_link=payment_link['url']
        )
        
        # Step 11: Send WhatsApp notification
        whatsapp_result = None
        whatsapp_message_id = None
        
        if customer_phone:
            whatsapp_result = whatsapp_service.send_message(
                to_phone=customer_phone,
                message=notification_message
            )
            whatsapp_message_id = whatsapp_result.get('message_id')
        
        # Step 12: Log notification
        notification_data = {
            "bill_id": bill_id,
            "customer_id": customer_id,
            "channel": "whatsapp",
            "message": notification_message,
            "status": "sent" if whatsapp_result and whatsapp_result.get('success') else "failed",
            "whatsapp_message_id": whatsapp_message_id,
            "sent_at": datetime.now()
        }
        
        logger.info(f"Logging notification for bill {bill_id}")
        db_service.log_notification(notification_data)
        
        # Step 13: Return success response with detailed breakdown
        logger.info(f"Workflow completed successfully for bill {bill_id}")
        return jsonify({
            "success": True,
            "bill_id": bill_id,
            "validation": validation_result,
            "calculation": bill_calculation,
            "payment_link": payment_link['url'],
            "notification_sent": whatsapp_result.get('success') if whatsapp_result else False
        }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "billing-api"}), 200


@app.route('/webhook/meter-reading/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is running"""
    return jsonify({
        "message": "Billing API is running",
        "endpoints": {
            "meter_reading": "/webhook/meter-reading (POST)",
            "bill_status": "/api/bills/<bill_id> (GET)",
            "customer_bills": "/api/bills/customer/<customer_id> (GET)",
            "stripe_webhook": "/webhook/stripe (POST)",
            "health": "/health (GET)"
        }
    }), 200


@app.route('/api/bills/<int:bill_id>', methods=['GET'])
@handle_api_errors
def get_bill_status(bill_id):
    """Get bill status and details"""
    logger.debug(f"Fetching bill status for bill {bill_id}")
    bill = db_service.get_bill_by_id(bill_id)
    
    if not bill:
        logger.warning(f"Bill {bill_id} not found")
        return jsonify({"error": "Bill not found"}), 404
    
    logger.info(f"Retrieved bill {bill_id} with status {bill.get('status')}")
    return jsonify({
        "success": True,
        "bill": bill
    }), 200


@app.route('/api/bills/customer/<customer_id>', methods=['GET'])
@handle_api_errors
def get_customer_bills(customer_id):
    """Get all bills for a customer"""
    logger.debug(f"Fetching bills for customer {customer_id}")
    limit = request.args.get('limit', 10, type=int)
    bills = db_service.get_bills_by_customer(customer_id, limit)
    
    logger.info(f"Retrieved {len(bills)} bills for customer {customer_id}")
    return jsonify({
        "success": True,
        "customer_id": customer_id,
        "count": len(bills),
        "bills": bills
    }), 200


@app.route('/webhook/stripe', methods=['POST'])
@handle_api_errors
def stripe_webhook():
    """
    Stripe webhook endpoint for payment events
    
    Workflow:
    1. Verify webhook signature
    2. Check if payment successful
    3. Mark bill as paid in database
    4. Save payment details to payment_events table
    5. Generate AI thank you message
    6. Send Discord notification
    7. Log notification in database
    
    Setup in Stripe Dashboard:
    1. Go to Developers → Webhooks
    2. Add endpoint: https://your-domain.com/webhook/stripe
    3. Select events: checkout.session.completed, payment_intent.succeeded
    4. Copy webhook signing secret to .env
    """
    with LogContext(logger, "Process Stripe webhook"):
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        # Step 1: Verify webhook signature
        if not Config.STRIPE_WEBHOOK_SECRET or Config.STRIPE_WEBHOOK_SECRET == "whsec_your_webhook_secret":
            # Parse event without verification (TESTING ONLY)
            logger.warning("Processing Stripe webhook without signature verification (TEST MODE)")
            event = json.loads(payload)
        else:
            # Verify webhook signature (PRODUCTION)
            try:
                import stripe
                event = stripe.Webhook.construct_event(
                    payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
                )
                logger.info("✅ Stripe webhook signature verified")
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid Stripe webhook signature: {e}")
                return jsonify({"error": "Invalid signature"}), 400
        
        event_type = event.get('type')
        event_data = event.get('data', {}).get('object', {})
        logger.info(f"Processing Stripe event: {event_type}")
        
        # Step 2: Handle checkout session completed
        if event_type == 'checkout.session.completed':
            metadata = event_data.get('metadata', {})
            bill_id = metadata.get('bill_id')
            customer_id = metadata.get('customer_id')
            payment_status = event_data.get('payment_status')
            amount_total = event_data.get('amount_total', 0) / 100  # Convert from paise to rupees
            
            # Step 3: Check if payment successful
            if bill_id and payment_status == 'paid':
                logger.info(f"💰 Payment completed for bill {bill_id}")
                
                # Step 4: Mark bill as paid
                db_service.update_bill_status(
                    bill_id=int(bill_id),
                    status='paid',
                    payment_date=datetime.now().isoformat()
                )
                logger.info(f"✅ Bill {bill_id} marked as paid")
                
                # Step 5: Save payment details
                db_service.log_payment_event({
                    'bill_id': int(bill_id),
                    'event_type': event_type,
                    'payment_link_id': metadata.get('payment_link_id'),
                    'stripe_event_id': event.get('id'),
                    'amount': amount_total,
                    'currency': event_data.get('currency', 'inr'),
                    'status': 'succeeded',
                    'customer_id': customer_id,
                    'event_data': json.dumps(event_data),
                    'received_at': datetime.now().isoformat()
                })
                logger.info(f"💾 Payment details saved for bill {bill_id}")
                
                # Step 6: Generate AI thank you message
                try:
                    ai_message = ai_service.generate_payment_confirmation_message(
                        customer_id=customer_id,
                        bill_id=bill_id,
                        amount=amount_total
                    )
                except Exception as e:
                    logger.warning(f"AI message generation failed, using default: {e}")
                    ai_message = f"Thank you for your payment of ₹{amount_total:.2f}! Your bill #{bill_id} has been paid successfully."
                
                # Step 7: Send Discord notification
                from services.discord_service import DiscordService
                discord_service = DiscordService()
                
                discord_result = discord_service.send_payment_confirmation(
                    customer_id=customer_id,
                    bill_id=str(bill_id),
                    amount=amount_total,
                    payment_date=datetime.now().isoformat()
                )
                
                if discord_result.get('success'):
                    logger.info(f"✅ Discord payment confirmation sent for bill {bill_id}")
                else:
                    logger.error(f"❌ Discord notification failed for bill {bill_id}")
                
                # Step 8: Log notification
                db_service.log_notification({
                    'bill_id': int(bill_id),
                    'customer_id': customer_id,
                    'channel': 'discord',
                    'message': ai_message,
                    'status': 'sent' if discord_result.get('success') else 'failed',
                    'sent_at': datetime.now().isoformat()
                })
                logger.info(f"📝 Notification logged for bill {bill_id}")
                
                logger.info(f"🎉 Payment workflow completed successfully for bill {bill_id}")
        
        # Handle payment intent succeeded (alternative event)
        elif event_type == 'payment_intent.succeeded':
            payment_intent = event_data
            metadata = payment_intent.get('metadata', {})
            bill_id = metadata.get('bill_id')
            customer_id = metadata.get('customer_id')
            amount = payment_intent.get('amount', 0) / 100
            
            if bill_id:
                logger.info(f"Payment intent succeeded for bill {bill_id}")
                
                # Mark bill as paid
                db_service.update_bill_status(
                    bill_id=int(bill_id),
                    status='paid',
                    payment_date=datetime.now().isoformat()
                )
                
                # Save payment details
                db_service.log_payment_event({
                    'bill_id': int(bill_id),
                    'event_type': event_type,
                    'stripe_event_id': event.get('id'),
                    'amount': amount,
                    'currency': payment_intent.get('currency', 'inr'),
                    'status': 'succeeded',
                    'customer_id': customer_id,
                    'event_data': json.dumps(event_data),
                    'received_at': datetime.now().isoformat()
                })
                
                logger.info(f"✅ Bill {bill_id} payment confirmed via payment_intent")
        
        return jsonify({"received": True, "event": event_type}), 200


@app.route('/api/bills/<int:bill_id>/status', methods=['PUT'])
@handle_api_errors
def update_bill_status_manual(bill_id):
    """Manually update bill status (for admin)"""
    logger.debug(f"Manually updating status for bill {bill_id}")
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['pending', 'paid', 'failed', 'cancelled']:
        logger.warning(f"Invalid status provided: {new_status}")
        return jsonify({"error": "Invalid status"}), 400
    
    updated_bill = db_service.update_bill_status(
        bill_id=bill_id,
        status=new_status,
        payment_date=data.get('payment_date')
    )
    
    logger.info(f"Bill {bill_id} status updated to {new_status}")
    return jsonify({
        "success": True,
        "bill": updated_bill
    }), 200


@app.route('/api/scheduler/status', methods=['GET'])
@handle_api_errors
def get_scheduler_status():
    """Get status of all scheduled jobs"""
    logger.debug("Fetching scheduler status")
    jobs = scheduler.get_job_status()
    
    return jsonify({
        "success": True,
        "scheduler_running": scheduler.scheduler.running,
        "jobs": jobs
    }), 200


@app.route('/api/scheduler/jobs/<job_id>/run', methods=['POST'])
@handle_api_errors
def run_scheduled_job(job_id):
    """Manually trigger a scheduled job"""
    logger.info(f"Manually triggering job: {job_id}")
    result = scheduler.run_job_now(job_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
