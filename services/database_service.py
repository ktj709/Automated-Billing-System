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

# Import Supabase/PostgREST error type so we can handle
# duplicate-key (23505) constraints gracefully in create_bill.
try:
    from postgrest.exceptions import APIError as PostgrestAPIError
except Exception:  # pragma: no cover - fallback when library not present
    PostgrestAPIError = Exception


class DatabaseService:
    """PostgreSQL database service for billing operations"""

    # Duplicate insert_meter_reading removed from here (lines 22-47). 
    # See the implemented method further down in the class.
    
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
                # New schema: readings are stored in 'readings' and linked to the
                # 'meters' table via an integer meter_id. The caller may pass
                # either a meter_number (e.g. "87923504") or a numeric ID.

                meter_pk = None

                # 1) Try resolving by meter_number first (most common from UI)
                try:
                    meters_resp = (
                        self.supabase
                        .table('meters')
                        .select('id')
                        .eq('meter_number', str(meter_id))
                        .limit(1)
                        .execute()
                    )
                    if meters_resp.data:
                        meter_pk = meters_resp.data[0]['id']
                except Exception as e:
                    logger.warning(f"Error resolving meter_number for {meter_id}: {e}")

                # 2) If not found, fall back to treating the input as a numeric id
                if meter_pk is None:
                    try:
                        meter_pk = int(str(meter_id))
                    except (TypeError, ValueError):
                        meter_pk = None

                if meter_pk is None:
                    logger.info(f"No meter found for identifier {meter_id}; returning empty history")
                    return []

                response = (
                    self.supabase
                    .table('readings')
                    .select('*')
                    .eq('meter_id', meter_pk)
                    .order('reading_date', desc=True)
                    .limit(limit)
                    .execute()
                )

                logger.info(f"Retrieved {len(response.data or [])} readings for meter {meter_id} (meter_id={meter_pk})")
                return response.data or []
        except Exception as e:
            logger.error(f"Error fetching historical readings for {meter_id}: {e}")
            raise
        
        query = """
            SELECT * FROM readings 
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
                # New schema: use the consolidated 'readings' table
                response = (
                    self.supabase
                    .table('readings')
                    .select('*')
                    .order('reading_date', desc=True)
                    .limit(limit)
                    .execute()
                )
                logger.info(f"Retrieved {len(response.data or [])} total readings from 'readings'")
                return response.data or []
        except Exception as e:
            logger.error(f"Error fetching all readings: {e}")
            raise
        
        query = """
            SELECT * FROM readings 
            ORDER BY reading_date DESC 
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (limit,))
                results = cur.fetchall()
                return [dict(row) for row in results]

    def get_monthly_readings_count(self, year: int, month: int) -> int:
        """Count readings in the new 'readings' table for a given month.

        This is used for the Field Engineer dashboard progress counter.
        It only considers rows in the new schema (readings table), not the
        legacy 'meter_readings' table.
        """

        logger.debug(f"Counting readings for {year}-{month:02d} in new schema")

        from datetime import date as _date

        try:
            if self.use_supabase:
                # Compute month start and start of next month
                start = _date(year, month, 1)
                if month == 12:
                    next_month = _date(year + 1, 1, 1)
                else:
                    next_month = _date(year, month + 1, 1)

                response = (
                    self.supabase
                    .table('readings')
                    .select('id, reading_date, reading_value')
                    .gte('reading_date', start.isoformat())
                    .lt('reading_date', next_month.isoformat())
                    .execute()
                )

                rows = response.data or []

                # Only count actual readings (value > 0), mirroring old logic
                count = 0
                for r in rows:
                    try:
                        if float(r.get('reading_value', 0) or 0) > 0:
                            count += 1
                    except Exception:
                        continue

                logger.info(f"Monthly readings count for {year}-{month:02d}: {count}")
                return count
        except Exception as e:
            logger.error(f"Error counting monthly readings for {year}-{month:02d}: {e}")
            return 0

        # Legacy non-Supabase path is no-op for the new schema
        return 0
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def create_bill(self, bill_data: Dict) -> Dict:
        """Create a single bill record.

        This is used by the Streamlit dashboards, API, and scheduler
        when generating an individual bill from a calculated amount.
        """
        logger.debug(f"Creating bill for customer {bill_data.get('customer_id')} meter {bill_data.get('meter_id')}")

        # Hard safety: never create *new* November 2025 bills.
        #
        # We still allow future bills whose period STARTS in November
        # 2025 but ENDS in a later month (e.g. 2025‑11‑30 → 2026‑01‑03)
        # so that newer bills can depend on the final November
        # readings without altering any existing November bills.
        try:
            end_raw = bill_data.get('billing_period_end')
            end_dt = datetime.fromisoformat(str(end_raw)).date() if end_raw else None

            # Block only when the bill's END date is in November 2025,
            # which corresponds to the historical November bills we
            # want to keep frozen.
            if end_dt and end_dt.year == 2025 and end_dt.month == 11:
                logger.warning("Single-bill creation for November 2025 is locked (end date in 2025-11); skipping insert.")
                return {
                    "status": "error",
                    "message": "Billing for November 2025 is locked and cannot be modified.",
                }
        except Exception:
            # If date parsing fails, fall through and let DB/validation handle it
            pass

        try:
            if self.use_supabase:
                # Map legacy bill_data into the new Supabase "bills" schema.
                flat_units = bill_data.get('consumption_kwh') or bill_data.get('flat_units') or 0.0
                motor_units = bill_data.get('motor_units', 0.0)
                total_units = bill_data.get('total_units') or (flat_units + motor_units)

                # Resolve flat_id safely for Supabase:
                # 1) Prefer explicit bill_data["flat_id"] when provided.
                # 2) Next, resolve via the meter identifier (meter number or id)
                #    from the `meters` table, since the workflow now treats
                #    the meter number as the primary identifier.
                # 3) Finally, fall back to interpreting bill_data["customer_id"]
                #    as either a numeric flat_id or a flat code.
                resolved_flat_id = bill_data.get('flat_id')

                # Step 2: Try resolving from meter identifier
                if resolved_flat_id is None:
                    meter_identifier = bill_data.get('meter_id')
                    if meter_identifier is not None:
                        meter_flat_id = None

                        # 2a) Resolve by meter_number (string, e.g. "19152159")
                        try:
                            meters_resp = (
                                self.supabase
                                .table('meters')
                                .select('id, flat_id')
                                .eq('meter_number', str(meter_identifier))
                                .limit(1)
                                .execute()
                            )
                            if meters_resp.data:
                                meter_flat_id = meters_resp.data[0].get('flat_id')
                        except Exception as meter_lookup_err:
                            logger.warning(
                                "Error resolving flat_id from meter_number %s: %s",
                                meter_identifier,
                                meter_lookup_err,
                            )

                        # 2b) If not found, treat meter_identifier as a numeric meter id
                        if meter_flat_id is None:
                            try:
                                meter_pk = int(str(meter_identifier))
                                meters_resp = (
                                    self.supabase
                                    .table('meters')
                                    .select('id, flat_id')
                                    .eq('id', meter_pk)
                                    .limit(1)
                                    .execute()
                                )
                                if meters_resp.data:
                                    meter_flat_id = meters_resp.data[0].get('flat_id')
                            except (TypeError, ValueError):
                                meter_flat_id = None
                            except Exception as meter_id_lookup_err:
                                logger.warning(
                                    "Error resolving flat_id from meter id %s: %s",
                                    meter_identifier,
                                    meter_id_lookup_err,
                                )

                        if meter_flat_id is not None:
                            resolved_flat_id = meter_flat_id

                # Step 3: Fall back to customer identifier (unit/flat code or numeric flat id)
                if resolved_flat_id is None:
                    customer_identifier = bill_data.get('customer_id')
                    if customer_identifier is not None:
                        try:
                            # If the customer identifier is already a numeric
                            # flat ID (e.g. from another flow), use it.
                            resolved_flat_id = int(customer_identifier)
                        except (TypeError, ValueError):
                            # Treat it as a unit/flat code, e.g. "5BHK-B17-FF",
                            # and resolve via the `flats.code` column. The
                            # production schema stores codes like "B17-FF",
                            # so we normalise the identifier by stripping any
                            # leading type prefix and keeping only the last two
                            # segments.
                            try:
                                raw = str(customer_identifier).strip().upper()
                                parts = [p for p in raw.split('-') if p]
                                if len(parts) >= 2:
                                    norm_code = '-'.join(parts[-2:])
                                else:
                                    norm_code = raw

                                flat_resp = (
                                    self.supabase
                                    .table('flats')
                                    .select('id')
                                    .eq('code', norm_code)
                                    .limit(1)
                                    .execute()
                                )
                                if flat_resp.data:
                                    resolved_flat_id = flat_resp.data[0]['id']
                                else:
                                    logger.warning(
                                        "Could not resolve flat_id for customer identifier %s (normalised to %s)",
                                        customer_identifier,
                                        norm_code,
                                    )
                            except Exception as lookup_err:
                                logger.error(
                                    "Error looking up flat_id for customer identifier %s: %s",
                                    customer_identifier,
                                    lookup_err,
                                )

                if resolved_flat_id is None:
                    # We can't safely insert a bill without a valid flat_id
                    # in the new normalized schema.
                    logger.error(
                        "Aborting bill creation: flat_id could not be resolved from bill_data=%s",
                        bill_data,
                    )
                    return {
                        "status": "error",
                        "message": "Could not resolve flat for this bill; please check the unit ID/flat mapping.",
                    }

                # Determine the total amount carefully. We must not use the
                # Python ``or`` operator here because ``0.0`` is falsy and
                # would cause us to fall back to a missing ``total_amount``
                # key, resulting in ``NULL`` being sent to a NOT NULL column.
                amount_value = bill_data.get('amount')
                if amount_value is None:
                    amount_value = bill_data.get('total_amount')

                if amount_value is None:
                    logger.error(
                        "Aborting bill creation: total_amount is missing in bill_data=%s",
                        bill_data,
                    )
                    return {
                        "status": "error",
                        "message": "Bill total amount is missing; cannot create bill.",
                    }

                # Derive a due_date for the normalized Supabase schema.
                # The live "bills" table treats due_date as NOT NULL,
                # and the existing flows use the billing_period_end as
                # the logical due date (see scheduler_service and
                # Discord notifications). To stay consistent and avoid
                # constraint violations, we mirror that behaviour here.
                billing_period_end = bill_data.get('billing_period_end')
                due_date = bill_data.get('due_date') or billing_period_end

                supabase_payload = {
                    'flat_id': resolved_flat_id,
                    'billing_period_start': bill_data.get('billing_period_start'),
                    'billing_period_end': billing_period_end,
                    'due_date': due_date,
                    'flat_units': flat_units,
                    'motor_units': motor_units,
                    'total_units': total_units,
                    'total_amount': amount_value,
                    'status': bill_data.get('status', 'pending'),
                    'created_at': bill_data.get('created_at', datetime.now().isoformat()),
                }

                response = self.supabase.table('bills').insert(supabase_payload).execute()
                logger.info("Created bill via Supabase")
                return response.data[0] if response.data else {}
        except PostgrestAPIError as e:
            # Handle unique-constraint violations on
            # (flat_id, billing_period_start) gracefully so the
            # workflow can show a friendly message instead of a
            # low-level traceback.
            msg = str(e)
            if 'bills_flat_id_billing_period_start_key' in msg or '23505' in msg:
                logger.warning(
                    "Duplicate bill detected for flat_id=%s and billing_period_start=%s; attempting alternate start date.",
                    resolved_flat_id,
                    bill_data.get('billing_period_start'),
                )

                # Business requirement: never overwrite existing
                # bills, but *do* store the new bill as a separate
                # row even if there is already a bill for that flat
                # and logical period. To respect the database
                # uniqueness constraint on
                # (flat_id, billing_period_start), we retry the
                # insert with an adjusted start date that is still
                # meaningful but distinct and guaranteed not to
                # collide with existing rows for this flat.
                try:
                    # 1) Find the latest existing billing_period_start
                    # for this flat, so we can move forward in time.
                    latest_start = None
                    try:
                        latest_resp = (
                            self.supabase
                            .table('bills')
                            .select('billing_period_start')
                            .eq('flat_id', resolved_flat_id)
                            .order('billing_period_start', desc=True)
                            .limit(1)
                            .execute()
                        )
                        if latest_resp.data:
                            latest_start_raw = latest_resp.data[0].get('billing_period_start')
                            if latest_start_raw:
                                latest_start = datetime.fromisoformat(str(latest_start_raw)).date()
                    except Exception as lookup_err:
                        logger.warning(
                            "Error looking up latest billing_period_start for flat_id=%s: %s",
                            resolved_flat_id,
                            lookup_err,
                        )

                    # 2) Use the bill's END date as the natural
                    # lower bound for the alternate start, but if
                    # there are already later starts, move one day
                    # beyond the latest to keep it unique.
                    end_raw = bill_data.get('billing_period_end')
                    try:
                        end_dt = datetime.fromisoformat(str(end_raw)).date() if end_raw else None
                    except Exception:
                        end_dt = None

                    candidate = end_dt or (latest_start or datetime.now().date())
                    if latest_start and latest_start >= candidate:
                        from datetime import timedelta as _timedelta
                        candidate = latest_start + _timedelta(days=1)

                    alt_start = candidate.isoformat()

                    alt_payload = dict(supabase_payload)
                    alt_payload['billing_period_start'] = alt_start

                    alt_resp = self.supabase.table('bills').insert(alt_payload).execute()
                    logger.info(
                        "Created bill via Supabase using alternate billing_period_start=%s to avoid duplicate.",
                        alt_start,
                    )
                    return alt_resp.data[0] if alt_resp.data else {}
                except PostgrestAPIError as e2:
                    # If even the alternate start collides, fall
                    # back to a clear error message so the caller
                    # knows a new row was not stored.
                    logger.error(
                        "Failed to create alternate bill for flat_id=%s after duplicate: %s",
                        resolved_flat_id,
                        e2,
                    )
                    return {
                        "status": "error",
                        "message": "A bill for this flat and billing period already exists in Supabase; no additional copy could be stored.",
                    }

            logger.error(f"Error creating bill via Supabase: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating bill via Supabase: {e}")
            raise

        # Legacy PostgreSQL path
        query = """
            INSERT INTO bills (
                customer_id,
                meter_id,
                billing_period_start,
                billing_period_end,
                consumption_kwh,
                amount,
                status,
                created_at
            ) VALUES (
                %(customer_id)s,
                %(meter_id)s,
                %(billing_period_start)s,
                %(billing_period_end)s,
                %(consumption_kwh)s,
                %(amount)s,
                %(status)s,
                %(created_at)s
            ) RETURNING *
        """

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, bill_data)
                result = cur.fetchone()
                conn.commit()
                logger.info("Created bill via PostgreSQL")
                return dict(result)

    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def generate_bills_for_month(self, billing_period_start: str, billing_period_end: str, due_date: str) -> Dict:
        """Trigger bulk bill generation via database RPC.

        This is used for the admin dashboard bulk generation flow and
        operates on a full billing period rather than a single bill.
        """
        logger.debug(f"Triggering bill generation for period {billing_period_start} to {billing_period_end}")

        try:
            if self.use_supabase:
                # Protect historical November 2025 data from being regenerated
                try:
                    start_dt = datetime.fromisoformat(billing_period_start).date()
                    end_dt = datetime.fromisoformat(billing_period_end).date()
                    if (start_dt.year == 2025 and start_dt.month == 11) or \
                       (end_dt.year == 2025 and end_dt.month == 11):
                        logger.warning("Billing for November 2025 is locked; skipping RPC call.")
                        return {
                            "status": "error",
                            "message": "Billing for November 2025 is locked and cannot be regenerated.",
                        }
                except Exception:
                    # If parsing fails, fall through and let RPC handle/validate dates
                    pass

                params = {
                    'p_billing_period_start': billing_period_start,
                    'p_billing_period_end': billing_period_end,
                    'p_due_date': due_date
                }
                response = self.supabase.rpc('generate_bills_for_month', params).execute()

                # The RPC returns a set of bills. We can return summary or list.
                logger.info("Generated bills via RPC")
                return {"status": "success", "data": response.data}

        except Exception as e:
            logger.error(f"Error generating bills: {e}")
            raise

        return {"status": "error", "message": "Legacy mode not supported for RPC billing"}
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def update_bill_payment_info(self, bill_id: int, payment_link: str, payment_link_id: str) -> Dict:
        """Update bill with payment link information"""
        logger.debug(f"Updating payment info for bill {bill_id}")
        
        try:
            if self.use_supabase:
                # Supabase schema no longer stores payment_link fields on
                # bills. To avoid schema cache errors entirely, we no longer
                # issue any UPDATE against the Supabase `bills` table from
                # this method. Payment tracking is handled via Stripe and
                # webhooks instead.
                logger.info(
                    "Skipping bill payment_link update on Supabase for bill %s; "
                    "Stripe/webhooks handle payment state.",
                    bill_id,
                )
                return {"status": "skipped"}
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
                # Supabase `notifications.bill_id` is an integer FK. The
                # UI sometimes uses a string fallback ID like
                # "BILL_20260101033825" purely for display. Before
                # inserting, coerce bill_id to an int when possible;
                # otherwise, omit it so the column is NULL and we avoid
                # integer cast errors (22P02).
                payload = dict(notification_data)
                bill_id_val = payload.get('bill_id')
                if bill_id_val is not None:
                    try:
                        payload['bill_id'] = int(bill_id_val)
                    except (TypeError, ValueError):
                        logger.warning(
                            "Skipping non-numeric bill_id %s in notification payload; setting to NULL.",
                            bill_id_val,
                        )
                        payload['bill_id'] = None

                response = self.supabase.table('notifications').insert(payload).execute()
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
        """
        Insert a new meter reading into 'readings' table.
        Calculates consumption based on the previous reading (e.g. November reading).
        """
        meter_id = reading_data.get('meter_id')
        current_val = float(reading_data.get('reading_value', 0))
        reading_date = reading_data.get('reading_date')
        
        logger.debug(f"Inserting reading for meter {meter_id}: {current_val} on {reading_date}")
        
        try:
            if self.use_supabase:
                # 1. Fetch Previous Reading to calculate consumption
                # We want the latest reading BEFORE the current reading date
                prev_resp = self.supabase.table('readings')\
                    .select('reading_value, reading_date')\
                    .eq('meter_id', meter_id)\
                    .lt('reading_date', reading_date)\
                    .order('reading_date', desc=True)\
                    .limit(1)\
                    .execute()
                
                previous_val = 0.0
                if prev_resp.data and len(prev_resp.data) > 0:
                    previous_val = float(prev_resp.data[0]['reading_value'])
                    logger.info(f"Found previous reading: {previous_val}")
                else:
                    logger.info("No previous reading found (First entry)")

                # 2. Calculate Consumption
                consumption = current_val - previous_val
                if consumption < 0:
                     # Fallback logic? Or just log warning? 
                     # For now, let's allow it but warn, or cap at 0 if reset?
                     # Assuming normal operation:
                     logger.warning(f"Negative consumption detected! {current_val} - {previous_val} = {consumption}")
                
                # 3. Prepare Payload for 'readings' table
                # Schema: id, meter_id, reading_date, reading_value, consumption
                payload = {
                    "meter_id": meter_id,
                    "reading_date": reading_date,
                    "reading_value": current_val,
                    "consumption": consumption
                }
                
                # Check for image path if we ever add it to the new schema
                # if 'meter_image_path' in reading_data:
                #     payload['image_path'] = reading_data['meter_image_path']

                response = self.supabase.table('readings').insert(payload).execute()
                result = response.data[0] if response.data else {}
                logger.info(f"Inserted reading ID {result.get('id')} for meter {meter_id}")
                return result

        except Exception as e:
            logger.error(f"Error inserting meter reading: {e}")
            raise
        
        # Legacy Postgres Fallback (Cleaned up to be minimal or raise error as we are moving to Supabase)
        logger.warning("Legacy PostgreSQL insertion attempting...")
        return {} # Placeholder to prevent usage
    
    def get_unbilled_readings(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve 'readings' that do not have a corresponding 'bill'.
        New Schema: bills.flat_reading_id links to readings.id
        """
        logger.debug(f"Fetching unbilled readings (limit: {limit})")
        
        try:
            if self.use_supabase:
                # 1. Get IDs of readings that are already linked to bills
                #    via either flat_reading_id (normal bills) OR
                #    motor_reading_id (motor share bills). Any such
                #    readings must be treated as "billed" so that the
                #    UI never offers to delete them, which would violate
                #    the foreign key constraints seen in production.

                billed_resp = (
                    self.supabase
                    .table('bills')
                    .select('flat_reading_id, motor_reading_id')
                    .execute()
                )

                billed_ids: set[int] = set()
                if billed_resp.data:
                    for item in billed_resp.data:
                        fr = item.get('flat_reading_id')
                        mr = item.get('motor_reading_id')
                        if fr is not None:
                            billed_ids.add(fr)
                        if mr is not None:
                            billed_ids.add(mr)

                # 2. Get latest readings and filter out any that are
                #    already referenced by a bill.
                query = (
                    self.supabase
                    .table('readings')
                    .select('*')
                    .order('reading_date', desc=True)
                    .limit(limit)
                )

                response = query.execute()
                candidates = response.data or []

                unbilled = [r for r in candidates if r.get('id') not in billed_ids]

                logger.info(f"Found {len(unbilled)} unbilled readings")
                return unbilled

        except Exception as e:
            logger.error(f"Error fetching unbilled readings: {e}")
            return []
        
        return []
    
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

    def get_active_meters(self) -> List[Dict]:
        """Get list of active meters/flats from the database (registry)"""
        logger.debug("Fetching active meters registry via Joined Query")
        try:
            if self.use_supabase:
                # Execute JOIN query to get meter + flat + owner details
                # Note: This heavily relies on Supabase ability to run raw SQL or we construct a complex join via parameters
                # Since we have the key, we can use the 'rpc' if one exists, or try a direct select with joins if using the py client properly.
                # However, the python client `supabase-py` supports foreign key joins.
                
                # Query: Meters -> Flats -> Owners
                response = self.supabase.table('meters')\
                    .select('id, meter_number, status, flats(code, floor_id), flat_id')\
                    .eq('status', 'Active')\
                    .execute()
                
                # We need to manually flatten this or handle it in the UI. 
                # Better: Use a helper function or raw SQL if we can.
                # Let's try to stick to the client for now.
                # Problem: We need Owner Name. Meters -> Flats -> Flat_Owners -> Owners
                
                # Let's fallback to a raw SQL execution for simplicity and performance as the joins are deep
                # NOTE: The provided supabase client might not support raw sql directly without RPC.
                # But we can use the `rpc` called `get_active_meters_view` if we created one? 
                # The user's roadmap suggested a SQL query. Let's try to implement that logic in Python processing
                # by fetching linked entities.
                
                # Actually, let's look at what we need: Meter ID, Flat No, Floor (maybe), Client Name.
                
                # Try fetching meter with Nested Resource
                # meters (id, meter_number) -> flats (code, floor_id) -> flat_owners (owner_id) -> owners (name)
                # Syntax: select('*, flats(code, flat_owners(owners(name)))')
                
                # But wait, looking at schema:
                response = self.supabase.table('meters')\
                    .select('id, meter_number, flats!inner(code, floor_id, type_id, flat_owners!inner(owners!inner(name)), flat_types!inner(name))')\
                    .eq('status', 'active')\
                    .execute()
                    
                # Fetch floors for mapping
                floors_resp = self.supabase.table('floors').select('*').execute()
                floor_map = {f['id']: f['code'] for f in floors_resp.data} if floors_resp.data else {}

                # Transform data to flat structure expected by UI
                meters = []
                if response.data:
                    for item in response.data:
                        try:
                            flat = item.get('flats') or {}
                            flat_owners = flat.get('flat_owners', [])
                            owner_name = "Unknown"
                            if flat_owners and isinstance(flat_owners, list) and len(flat_owners) > 0:
                                owner = flat_owners[0].get('owners')
                                if owner:
                                    owner_name = owner.get('name')
                            
                            floor_id = flat.get('floor_id')
                            floor_code = floor_map.get(floor_id, "")
                            
                            flat_type_obj = flat.get('flat_types') or {}
                            flat_type_name = flat_type_obj.get('name', "")
                            
                            # Construct Unit ID like '5BHK-B5-FF'
                            # Logic: {Type}-{FlatNo} (since FlatNo like B5-FF already includes floor)
                            unit_id = ""
                            if flat_type_name and flat.get('code'):
                                if floor_code and flat.get('code').endswith(f"-{floor_code}"):
                                    unit_id = f"{flat_type_name}-{flat.get('code')}"
                                elif floor_code:
                                     unit_id = f"{flat_type_name}-{flat.get('code')}-{floor_code}"
                                else:
                                     unit_id = f"{flat_type_name}-{flat.get('code')}"

                            meters.append({
                                "meter_id": item['id'],  # Integer ID from new schema
                                "meter_number": item['meter_number'], # Display string
                                "flat_no": flat.get('code'),
                                "client_name": owner_name,
                                "floor": floor_code, # Populated from map
                                "type": flat_type_name,
                                "unit_id": unit_id,
                                "status": "active"
                            })
                        except Exception as e:
                            logger.warning(f"Error parsing meter item: {e}")
                            continue

                logger.info(f"Retrieved {len(meters)} active meters from new schema")
                return meters

        except Exception as e:
            logger.error(f"Error fetching active meters: {e}")
            return []
        return []

    def update_meter_reading(self, reading_id: int, reading_data: Dict) -> Dict:
        """Update an existing meter reading"""
        logger.debug(f"Updating reading {reading_id}")
        try:
            if self.use_supabase:
                # New schema: update the 'readings' table instead of legacy 'meter_readings'
                response = self.supabase.table('readings')\
                    .update(reading_data)\
                    .eq('id', reading_id)\
                    .execute()
                result = response.data[0] if response.data else {}
                logger.info(f"Updated reading {reading_id}")
                return result
        except Exception as e:
            logger.error(f"Error updating reading {reading_id}: {e}")
            raise
        return {}
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def delete_reading(self, reading_id: int) -> bool:
        """Delete a meter reading by ID"""
        logger.debug(f"Deleting reading {reading_id}")
        try:
            if self.use_supabase:
                # New schema: readings are stored in the 'readings' table,
                # not the legacy 'meter_readings' table.
                self.supabase.table('readings').delete().eq('id', reading_id).execute()
                logger.info(f"Deleted reading {reading_id} from 'readings' table")
                return True
        except Exception as e:
            logger.error(f"Error deleting reading {reading_id}: {e}")
            return False
            
        # Legacy PostgreSQL fallback: keep behaviour consistent by
        # deleting from the new 'readings' table as well.
        query = "DELETE FROM readings WHERE id = %s"
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (reading_id,))
                conn.commit()
                return True
