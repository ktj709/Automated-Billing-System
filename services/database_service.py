from typing import List, Dict, Optional
from datetime import datetime
from config import Config
from utils.retry_decorator import retry, safe_execute, ErrorContext
from utils.logger import setup_logger

logger = setup_logger('database_service')

# Import psycopg2 only if needed (for legacy PostgreSQL)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    logger.warning("psycopg2 not installed - only Supabase mode available")


class DatabaseService:
    """PostgreSQL database service for billing operations"""

    def insert_meter_reading(self, reading_data: Dict) -> Dict:
        """Insert a new meter reading (field engineer submission)"""
        logger.debug(f"Inserting meter reading for meter {reading_data.get('meter_id')}")
        try:
            if self.use_supabase:
                response = self.supabase.table('meter_readings').insert(reading_data).execute()
                result = response.data[0] if response.data else {}
                logger.info(f"Inserted reading ID {result.get('id')} for meter {reading_data.get('meter_id')}")
                return result
        except Exception as e:
            logger.error(f"Error inserting meter reading: {e}")
            raise
        query = """
            INSERT INTO meter_readings (
                meter_id, engineer_id, reading_value, unit, reading_date, submitted_at, status
            ) VALUES (
                %(meter_id)s, %(engineer_id)s, %(reading_value)s, %(unit)s, %(reading_date)s, %(submitted_at)s, %(status)s
            ) RETURNING *
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, reading_data)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    def __init__(self):
        # Try Supabase REST API first, fallback to PostgreSQL
        if Config.SUPABASE_URL and Config.SUPABASE_KEY:
            self.use_supabase = True
            from supabase import create_client
            self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        else:
            self.use_supabase = False
            # Support both connection string and individual params
            if Config.POSTGRES_CONNECTION_STRING:
                self.connection_string = Config.POSTGRES_CONNECTION_STRING
                self.connection_params = None
            else:
                self.connection_string = None
                self.connection_params = {
                    'host': Config.POSTGRES_HOST,
                    'port': Config.POSTGRES_PORT,
                    'database': Config.POSTGRES_DB,
                    'user': Config.POSTGRES_USER,
                    'password': Config.POSTGRES_PASSWORD,
                    'sslmode': 'require'  # Required for Supabase
                }
    
    def get_connection(self):
        """Create a database connection (legacy PostgreSQL only)"""
        if self.use_supabase:
            raise Exception("Using Supabase REST API - direct connection not needed")
        if not HAS_PSYCOPG2:
            raise Exception("psycopg2 not installed - use Supabase configuration")
        if self.connection_string:
            return psycopg2.connect(self.connection_string, sslmode='require')
        else:
            return psycopg2.connect(**self.connection_params)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def get_historical_readings(self, meter_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve historical meter readings for a specific meter"""
        logger.debug(f"Fetching {limit} historical readings for meter {meter_id}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('meter_readings')\
                    .select('*')\
                    .eq('meter_id', meter_id)\
                    .order('reading_date', desc=True)\
                    .limit(limit)\
                    .execute()
                logger.info(f"Retrieved {len(response.data)} readings for meter {meter_id}")
                return response.data
        except Exception as e:
            logger.error(f"Error fetching historical readings for {meter_id}: {e}")
            raise
        
        query = """
            SELECT * FROM meter_readings 
            WHERE meter_id = %s 
            ORDER BY reading_date DESC 
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (meter_id, limit))
                results = cur.fetchall()
                return [dict(row) for row in results]
    
    def get_all_readings(self, limit: int = 10000) -> List[Dict]:
        """Retrieve ALL meter readings from database"""
        logger.debug(f"Fetching all readings (limit: {limit})")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('meter_readings')\
                    .select('*')\
                    .order('reading_date', desc=True)\
                    .limit(limit)\
                    .execute()
                logger.info(f"Retrieved {len(response.data)} total readings")
                return response.data
        except Exception as e:
            logger.error(f"Error fetching all readings: {e}")
            raise
        
        query = """
            SELECT * FROM meter_readings 
            ORDER BY reading_date DESC 
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                results = cur.fetchall()
                return [dict(row) for row in results]
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def create_bill(self, bill_data: Dict) -> Dict:
        """Create a new bill record"""
        logger.debug(f"Creating bill for customer {bill_data.get('customer_id')}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('bills').insert(bill_data).execute()
                result = response.data[0] if response.data else {}
                logger.info(f"Created bill ID {result.get('id')} for customer {bill_data.get('customer_id')}")
                return result
        except Exception as e:
            logger.error(f"Error creating bill: {e}")
            raise
        
        query = """
            INSERT INTO bills (
                customer_id, meter_id, billing_period_start, 
                billing_period_end, consumption_kwh, amount, 
                status, created_at
            ) VALUES (
                %(customer_id)s, %(meter_id)s, %(billing_period_start)s,
                %(billing_period_end)s, %(consumption_kwh)s, %(amount)s,
                %(status)s, %(created_at)s
            ) RETURNING *
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, bill_data)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def update_bill_payment_info(self, bill_id: int, payment_link: str, payment_link_id: str) -> Dict:
        """Update bill with payment link information"""
        logger.debug(f"Updating payment info for bill {bill_id}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('bills')\
                    .update({
                        'payment_link': payment_link,
                        'payment_link_id': payment_link_id,
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('id', bill_id)\
                    .execute()
                logger.info(f"Updated payment info for bill {bill_id}")
                return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error updating bill payment info for {bill_id}: {e}")
            raise
        
        query = """
            UPDATE bills 
            SET payment_link = %s, payment_link_id = %s, updated_at = NOW() 
            WHERE id = %s 
            RETURNING *
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (payment_link, payment_link_id, bill_id))
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def log_notification(self, notification_data: Dict) -> Dict:
        """Log a notification sent to customer"""
        logger.debug(f"Logging notification for customer {notification_data.get('customer_id')}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('notifications').insert(notification_data).execute()
                logger.info(f"Logged notification via {notification_data.get('channel')}")
                return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            raise
        
        query = """
            INSERT INTO notifications (
                bill_id, customer_id, channel, message, 
                status, whatsapp_message_id, sent_at
            ) VALUES (
                %(bill_id)s, %(customer_id)s, %(channel)s, %(message)s,
                %(status)s, %(whatsapp_message_id)s, %(sent_at)s
            ) RETURNING *
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, notification_data)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def update_bill_status(self, bill_id: int, status: str, payment_date: str = None) -> Dict:
        """Update bill payment status"""
        logger.debug(f"Updating bill {bill_id} status to {status}")
        
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Note: payment_date column doesn't exist in Supabase schema
            # Payment date is tracked in payment_events table instead
            
            if self.use_supabase:
                response = self.supabase.table('bills')\
                    .update(update_data)\
                    .eq('id', bill_id)\
                    .execute()
                logger.info(f"Updated bill {bill_id} status to {status}")
                return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error updating bill status for {bill_id}: {e}")
            raise
        
        if payment_date:
            query = """
                UPDATE bills 
                SET status = %s, payment_date = %s, updated_at = NOW() 
                WHERE id = %s 
                RETURNING *
            """
            params = (status, payment_date, bill_id)
        else:
            query = """
                UPDATE bills 
                SET status = %s, updated_at = NOW() 
                WHERE id = %s 
                RETURNING *
            """
            params = (status, bill_id)
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def get_bill_by_id(self, bill_id: int) -> Dict:
        """Get bill details by ID"""
        logger.debug(f"Fetching bill {bill_id}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('bills')\
                    .select('*')\
                    .eq('id', bill_id)\
                    .execute()
                result = response.data[0] if response.data else None
                if result:
                    logger.info(f"Retrieved bill {bill_id}")
                else:
                    logger.warning(f"Bill {bill_id} not found")
                return result
        except Exception as e:
            logger.error(f"Error fetching bill {bill_id}: {e}")
            raise
        
        query = "SELECT * FROM bills WHERE id = %s"
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (bill_id,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def get_bills_by_customer(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get all bills for a customer"""
        logger.debug(f"Fetching {limit} bills for customer {customer_id}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('bills')\
                    .select('*')\
                    .eq('customer_id', customer_id)\
                    .order('created_at', desc=True)\
                    .limit(limit)\
                    .execute()
                logger.info(f"Retrieved {len(response.data)} bills for customer {customer_id}")
                return response.data
        except Exception as e:
            logger.error(f"Error fetching bills for customer {customer_id}: {e}")
            raise
        
        query = """
            SELECT * FROM bills 
            WHERE customer_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (customer_id, limit))
                return [dict(row) for row in cur.fetchall()]
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def get_all_bills(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get all bills with optional status filter"""
        logger.debug(f"Fetching all bills (status={status}, limit={limit})")
        
        try:
            if self.use_supabase:
                query = self.supabase.table('bills').select('*')
                
                if status:
                    query = query.eq('status', status)
                
                query = query.order('created_at', desc=True)
                
                if limit:
                    query = query.limit(limit)
                
                response = query.execute()
                logger.info(f"Retrieved {len(response.data)} bills (status={status})")
                return response.data
        except Exception as e:
            logger.error(f"Error fetching bills: {e}")
            raise
        
        # Legacy PostgreSQL
        if status:
            query = "SELECT * FROM bills WHERE status = %s ORDER BY created_at DESC"
            params = (status,)
        else:
            query = "SELECT * FROM bills ORDER BY created_at DESC"
            params = ()
        
        if limit:
            query += " LIMIT %s"
            params = params + (limit,)
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def log_payment_event(self, event_data: Dict) -> Dict:
        """Log a payment webhook event"""
        logger.debug(f"Logging payment event: {event_data.get('event_type')}")
        
        try:
            if self.use_supabase:
                response = self.supabase.table('payment_events').insert(event_data).execute()
                logger.info(f"Logged payment event {event_data.get('stripe_event_id')}")
                return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error logging payment event: {e}")
            raise
        
        query = """
            INSERT INTO payment_events (
                bill_id, event_type, payment_link_id, 
                stripe_event_id, event_data, received_at
            ) VALUES (
                %(bill_id)s, %(event_type)s, %(payment_link_id)s,
                %(stripe_event_id)s, %(event_data)s, %(received_at)s
            ) RETURNING *
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, event_data)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    def insert_meter_reading(self, reading_data: Dict) -> Dict:
        """Insert a new meter reading"""
        if self.use_supabase:
            response = self.supabase.table('meter_readings').insert(reading_data).execute()
            return response.data[0] if response.data else {}
        
        query = """
            INSERT INTO meter_readings (
                meter_id, customer_id, reading_value, 
                reading_date, created_at
            ) VALUES (
                %(meter_id)s, %(customer_id)s, %(reading_value)s,
                %(reading_date)s, %(created_at)s
            ) RETURNING *
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, reading_data)
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def get_unbilled_readings(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve meter readings that don't have corresponding bills yet.
        A reading is considered unbilled if there's no bill with a billing_period_end 
        matching or after the reading_date for the same meter.
        """
        logger.debug(f"Fetching unbilled readings (limit: {limit})")
        
        try:
            if self.use_supabase:
                # Get all readings
                readings_response = self.supabase.table('meter_readings')\
                    .select('*')\
                    .order('reading_date', desc=True)\
                    .limit(limit * 2)\
                    .execute()
                
                all_readings = readings_response.data
                
                # Get all bills
                bills_response = self.supabase.table('bills')\
                    .select('meter_id, billing_period_end')\
                    .execute()
                
                bills = bills_response.data
                
                # Create a set of (meter_id, date) tuples for billed readings
                billed_readings = set()
                for bill in bills:
                    billed_readings.add((bill['meter_id'], bill['billing_period_end']))
                
                # Filter out readings that already have bills
                unbilled = []
                for reading in all_readings:
                    # Check if this reading has been billed
                    reading_date = reading['reading_date']
                    meter_id = reading['meter_id']
                    
                    # If no bill exists with this meter and date as billing_period_end, it's unbilled
                    if (meter_id, reading_date) not in billed_readings:
                        # Calculate estimated consumption (vs previous reading)
                        prev_readings = [r for r in all_readings 
                                       if r['meter_id'] == meter_id 
                                       and r['reading_date'] < reading_date]
                        
                        if prev_readings:
                            prev_reading = max(prev_readings, key=lambda x: x['reading_date'])
                            reading['estimated_consumption'] = reading['reading_value'] - prev_reading['reading_value']
                            reading['previous_reading'] = prev_reading['reading_value']
                        else:
                            reading['estimated_consumption'] = reading['reading_value']
                            reading['previous_reading'] = 0
                        
                        unbilled.append(reading)
                    
                    if len(unbilled) >= limit:
                        break
                
                logger.info(f"Found {len(unbilled)} unbilled readings")
                return unbilled
                
        except Exception as e:
            logger.error(f"Error fetching unbilled readings: {e}")
            raise
        
        # Legacy PostgreSQL - simplified version
        query = """
            SELECT r.* 
            FROM meter_readings r
            LEFT JOIN bills b ON r.meter_id = b.meter_id 
                AND r.reading_date = b.billing_period_end
            WHERE b.id IS NULL
            ORDER BY r.reading_date DESC
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                return [dict(row) for row in cur.fetchall()]
    
    def get_pending_bills_count(self) -> int:
        """Get count of unbilled meter readings"""
        logger.debug("Fetching unbilled readings count")
        
        try:
            unbilled = self.get_unbilled_readings(limit=1000)
            count = len(unbilled)
            logger.info(f"Total unbilled readings: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting unbilled count: {e}")
            return 0
