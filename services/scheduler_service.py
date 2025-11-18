"""
Automated Billing Scheduler
Uses APScheduler for scheduled jobs
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from services import DatabaseService, TariffRules, AIAgentService, PaymentService, WhatsAppService
from utils.logger import setup_logger, LogContext

logger = setup_logger('billing_scheduler')


class BillingScheduler:
    """Automated billing cycle scheduler"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = DatabaseService()
        self.ai_service = AIAgentService()
        self.payment_service = PaymentService()
        self.whatsapp_service = WhatsAppService()
        self.tariff_calculator = TariffRules()
        
        logger.info("Billing scheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        # Monthly bill generation - 1st of every month at 2:00 AM
        self.scheduler.add_job(
            self.generate_monthly_bills,
            trigger=CronTrigger(day=1, hour=2, minute=0),
            id='monthly_bill_generation',
            name='Generate Monthly Bills',
            replace_existing=True
        )
        
        # Payment reminder - Daily at 10:00 AM
        self.scheduler.add_job(
            self.send_payment_reminders,
            trigger=CronTrigger(hour=10, minute=0),
            id='payment_reminders',
            name='Send Payment Reminders',
            replace_existing=True
        )
        
        # Overdue bill check - Daily at 11:00 AM
        self.scheduler.add_job(
            self.mark_overdue_bills,
            trigger=CronTrigger(hour=11, minute=0),
            id='overdue_bills',
            name='Mark Overdue Bills',
            replace_existing=True
        )
        
        # Meter reading collection - Every Sunday at 8:00 AM
        self.scheduler.add_job(
            self.collect_meter_readings,
            trigger=CronTrigger(day_of_week='sun', hour=8, minute=0),
            id='meter_reading_collection',
            name='Collect Meter Readings',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Billing scheduler started with 4 jobs")
        self._log_scheduled_jobs()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Billing scheduler stopped")
    
    def _log_scheduled_jobs(self):
        """Log all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        logger.info(f"Scheduled jobs: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.name}: {job.next_run_time}")
    
    def generate_monthly_bills(self):
        """
        Generate bills for all active meters
        Runs on 1st of every month at 2:00 AM
        """
        with LogContext(logger, "Generate monthly bills"):
            try:
                # Get all active meters (this would come from a meters table)
                # For now, using sample data
                active_meters = self._get_active_meters()
                
                logger.info(f"Generating bills for {len(active_meters)} active meters")
                
                bills_generated = 0
                bills_failed = 0
                
                for meter in active_meters:
                    try:
                        bill = self._generate_bill_for_meter(meter)
                        if bill:
                            bills_generated += 1
                            logger.info(f"Bill generated for meter {meter['meter_id']}: ₹{bill['amount']}")
                        else:
                            bills_failed += 1
                            logger.warning(f"Failed to generate bill for meter {meter['meter_id']}")
                    except Exception as e:
                        bills_failed += 1
                        logger.error(f"Error generating bill for meter {meter['meter_id']}: {e}")
                
                logger.info(f"Monthly billing completed: {bills_generated} generated, {bills_failed} failed")
                
                return {
                    "success": True,
                    "bills_generated": bills_generated,
                    "bills_failed": bills_failed,
                    "total_meters": len(active_meters)
                }
                
            except Exception as e:
                logger.error(f"Monthly billing job failed: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    def send_payment_reminders(self):
        """
        Send payment reminders for pending bills
        Runs daily at 10:00 AM
        """
        with LogContext(logger, "Send payment reminders"):
            try:
                # Get pending bills due in next 3 days
                upcoming_bills = self._get_upcoming_due_bills(days=3)
                
                logger.info(f"Sending reminders for {len(upcoming_bills)} upcoming bills")
                
                reminders_sent = 0
                reminders_failed = 0
                
                for bill in upcoming_bills:
                    try:
                        # Generate reminder message
                        days_until_due = self._calculate_days_until_due(bill['billing_period_end'])
                        
                        if self.ai_service.enabled:
                            message = self.ai_service.generate_notification_message(
                                customer_id=bill['customer_id'],
                                bill_amount=bill['amount'],
                                consumption_kwh=bill['consumption_kwh'],
                                payment_link=bill.get('payment_link', '')
                            )
                        else:
                            message = f"""⚠️ Payment Reminder

Your electricity bill is due in {days_until_due} days.

Bill Amount: ₹{bill['amount']:.2f}
Consumption: {bill['consumption_kwh']} kWh
Due Date: {bill['billing_period_end']}

Pay now: {bill.get('payment_link', 'N/A')}

Avoid late fees - pay today!"""
                        
                        # Send reminder
                        customer_phone = self._get_customer_phone(bill['customer_id'])
                        if customer_phone:
                            result = self.whatsapp_service.send_message(customer_phone, message)
                            
                            if result.get('success'):
                                reminders_sent += 1
                                
                                # Log notification
                                self.db.log_notification({
                                    'bill_id': bill['id'],
                                    'customer_id': bill['customer_id'],
                                    'channel': 'whatsapp',
                                    'message': message,
                                    'status': 'sent',
                                    'whatsapp_message_id': result.get('message_id'),
                                    'sent_at': datetime.now().isoformat()
                                })
                            else:
                                reminders_failed += 1
                        else:
                            reminders_failed += 1
                            logger.warning(f"No phone number for customer {bill['customer_id']}")
                        
                    except Exception as e:
                        reminders_failed += 1
                        logger.error(f"Error sending reminder for bill {bill['id']}: {e}")
                
                logger.info(f"Payment reminders completed: {reminders_sent} sent, {reminders_failed} failed")
                
                return {
                    "success": True,
                    "reminders_sent": reminders_sent,
                    "reminders_failed": reminders_failed,
                    "total_bills": len(upcoming_bills)
                }
                
            except Exception as e:
                logger.error(f"Payment reminder job failed: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    def mark_overdue_bills(self):
        """
        Mark bills as overdue if past due date
        Runs daily at 11:00 AM
        """
        with LogContext(logger, "Mark overdue bills"):
            try:
                # Get pending bills past due date
                overdue_bills = self._get_overdue_bills()
                
                logger.info(f"Marking {len(overdue_bills)} bills as overdue")
                
                bills_marked = 0
                bills_failed = 0
                
                for bill in overdue_bills:
                    try:
                        # Update bill status to overdue
                        self.db.update_bill_status(
                            bill_id=bill['id'],
                            status='overdue'
                        )
                        bills_marked += 1
                        
                        # Send overdue notification
                        customer_phone = self._get_customer_phone(bill['customer_id'])
                        if customer_phone:
                            message = f"""🚨 OVERDUE BILL NOTICE

Your electricity bill is now OVERDUE.

Bill Amount: ₹{bill['amount']:.2f}
Due Date: {bill['billing_period_end']} (PAST DUE)
Late Fee: May apply

Pay immediately: {bill.get('payment_link', 'N/A')}

Contact customer service for assistance."""
                            
                            self.whatsapp_service.send_message(customer_phone, message)
                        
                    except Exception as e:
                        bills_failed += 1
                        logger.error(f"Error marking bill {bill['id']} as overdue: {e}")
                
                logger.info(f"Overdue marking completed: {bills_marked} marked, {bills_failed} failed")
                
                return {
                    "success": True,
                    "bills_marked": bills_marked,
                    "bills_failed": bills_failed,
                    "total_bills": len(overdue_bills)
                }
                
            except Exception as e:
                logger.error(f"Overdue billing job failed: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    def collect_meter_readings(self):
        """
        Collect meter readings from smart meters
        Runs every Sunday at 8:00 AM
        """
        with LogContext(logger, "Collect meter readings"):
            try:
                # Get all smart meters
                smart_meters = self._get_smart_meters()
                
                logger.info(f"Collecting readings from {len(smart_meters)} smart meters")
                
                readings_collected = 0
                readings_failed = 0
                
                for meter in smart_meters:
                    try:
                        # In production, this would call actual smart meter API
                        # For now, simulate reading collection
                        reading = self._simulate_meter_reading(meter)
                        
                        if reading:
                            readings_collected += 1
                            logger.info(f"Reading collected from meter {meter['meter_id']}: {reading['value']} kWh")
                        else:
                            readings_failed += 1
                        
                    except Exception as e:
                        readings_failed += 1
                        logger.error(f"Error collecting reading from meter {meter['meter_id']}: {e}")
                
                logger.info(f"Meter reading collection completed: {readings_collected} collected, {readings_failed} failed")
                
                return {
                    "success": True,
                    "readings_collected": readings_collected,
                    "readings_failed": readings_failed,
                    "total_meters": len(smart_meters)
                }
                
            except Exception as e:
                logger.error(f"Meter reading collection job failed: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
    
    # Helper methods
    
    def _get_active_meters(self) -> List[Dict]:
        """Get all active meters (would query meters table in production)"""
        # For now, return sample data
        return [
            {
                "meter_id": "METER001",
                "customer_id": "CUST001",
                "customer_phone": "+919876543210",
                "connected_load_kw": 7.0,
                "tariff_type": "residential"
            }
        ]
    
    def _get_smart_meters(self) -> List[Dict]:
        """Get all smart meters (would query meters table in production)"""
        return [
            {
                "meter_id": "METER001",
                "customer_id": "CUST001",
                "api_endpoint": "http://smart-meter-api/meter001"
            }
        ]
    
    def _generate_bill_for_meter(self, meter: Dict) -> Dict:
        """Generate a bill for a specific meter"""
        try:
            # Get latest reading
            readings = self.db.get_historical_readings(meter['meter_id'], limit=2)
            
            if len(readings) < 2:
                logger.warning(f"Not enough readings for meter {meter['meter_id']}")
                return None
            
            current_reading = readings[0]['reading_value']
            previous_reading = readings[1]['reading_value']
            
            # Calculate bill
            bill_calculation = self.ai_service.calculate_bill(
                current_reading=current_reading,
                previous_reading=previous_reading,
                meter_id=meter['meter_id'],
                customer_id=meter['customer_id'],
                connected_load_kw=meter.get('connected_load_kw', 7.0),
                tariff_type=meter.get('tariff_type', 'residential')
            )
            
            # Create bill in database
            bill_data = {
                "customer_id": meter['customer_id'],
                "meter_id": meter['meter_id'],
                "billing_period_start": readings[1]['reading_date'],
                "billing_period_end": readings[0]['reading_date'],
                "consumption_kwh": bill_calculation['consumption_kwh'],
                "amount": bill_calculation['total_amount'],
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            bill = self.db.create_bill(bill_data)
            
            # Create payment link
            payment_link = self.payment_service.create_payment_link(
                amount=bill_calculation['total_amount'],
                bill_id=bill['id'],
                customer_id=meter['customer_id'],
                meter_id=meter['meter_id'],
                description=f"Electricity Bill - {meter['meter_id']}"
            )
            
            # Update bill with payment link
            self.db.update_bill_payment_info(
                bill_id=bill['id'],
                payment_link=payment_link['url'],
                payment_link_id=payment_link['id']
            )
            
            # Send notification
            if meter.get('customer_phone'):
                message = self.ai_service.generate_notification_message(
                    customer_id=meter['customer_id'],
                    bill_amount=bill_calculation['total_amount'],
                    consumption_kwh=bill_calculation['consumption_kwh'],
                    payment_link=payment_link['url']
                )
                
                self.whatsapp_service.send_message(meter['customer_phone'], message)
            
            return {
                "id": bill['id'],
                "amount": bill_calculation['total_amount'],
                "consumption": bill_calculation['consumption_kwh']
            }
            
        except Exception as e:
            logger.error(f"Error generating bill for meter {meter['meter_id']}: {e}")
            return None
    
    def _get_upcoming_due_bills(self, days: int = 3) -> List[Dict]:
        """Get bills due in next N days"""
        # In production, this would query the database with a date filter
        # For now, return empty list (no upcoming bills in test data)
        try:
            # This would be a SQL query like:
            # SELECT * FROM bills 
            # WHERE status = 'pending' 
            # AND billing_period_end BETWEEN NOW() AND NOW() + INTERVAL days DAY
            return []
        except Exception as e:
            logger.error(f"Error fetching upcoming bills: {e}")
            return []
    
    def _get_overdue_bills(self) -> List[Dict]:
        """Get bills past due date and still pending"""
        # In production, this would query the database
        # SELECT * FROM bills WHERE status = 'pending' AND billing_period_end < NOW()
        try:
            return []
        except Exception as e:
            logger.error(f"Error fetching overdue bills: {e}")
            return []
    
    def _get_customer_phone(self, customer_id: str) -> str:
        """Get customer phone number (would query customers table)"""
        # Mock data
        customer_phones = {
            "CUST001": "+919876543210"
        }
        return customer_phones.get(customer_id)
    
    def _calculate_days_until_due(self, due_date: str) -> int:
        """Calculate days until bill due date"""
        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            now = datetime.now()
            delta = due - now
            return max(0, delta.days)
        except Exception as e:
            logger.error(f"Error calculating days until due: {e}")
            return 0
    
    def _simulate_meter_reading(self, meter: Dict) -> Dict:
        """Simulate collecting a meter reading (in production, call real API)"""
        # In production, this would call the smart meter API
        # For now, just log that we would collect it
        logger.info(f"Would collect reading from {meter.get('api_endpoint', 'N/A')}")
        return None
    
    def run_job_now(self, job_id: str):
        """Manually trigger a job (for testing)"""
        job = self.scheduler.get_job(job_id)
        if job:
            logger.info(f"Manually triggering job: {job_id}")
            job.func()
            return {"success": True, "job": job_id}
        else:
            logger.error(f"Job not found: {job_id}")
            return {"success": False, "error": f"Job {job_id} not found"}
    
    def get_job_status(self) -> List[Dict]:
        """Get status of all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]


# Global scheduler instance
_scheduler = None


def get_scheduler() -> BillingScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BillingScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
