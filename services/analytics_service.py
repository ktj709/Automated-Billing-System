import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
from services.database_service import DatabaseService
from utils.logger import setup_logger

logger = setup_logger('analytics_service')


class AnalyticsService:
    """Analytics and reporting service for billing system"""
    
    def __init__(self):
        self.db = DatabaseService()
        logger.info("Analytics service initialized")
    
    def get_monthly_revenue_report(self, year: int = None, month: int = None) -> Dict:
        """
        Generate monthly revenue report
        
        Args:
            year: Year for report (default: current year)
            month: Month for report (default: current month)
        
        Returns:
            Dictionary with revenue metrics
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        logger.info(f"Generating revenue report for {year}-{month:02d}")
        
        try:
            # Get all bills for the month using Supabase client
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            result = self.db.supabase.table('bills')\
                .select('*')\
                .gte('created_at', start_date.isoformat())\
                .lt('created_at', end_date.isoformat())\
                .execute()
            
            if result.data and len(result.data) > 0:
                df = pd.DataFrame(result.data)
                
                total_bills = len(df)
                total_revenue = df['amount'].sum()
                collected_revenue = df[df['status'] == 'paid']['amount'].sum()
                collected_revenue = df[df['status'] == 'paid']['amount'].sum()
                pending_revenue = df[df['status'].isin(['pending', 'generated', 'overdue'])]['amount'].sum()
                average_bill = df['amount'].mean()
                min_bill = df['amount'].min()
                max_bill = df['amount'].max()
                
                payment_success_rate = (collected_revenue / total_revenue * 100) if total_revenue > 0 else 0
                
                return {
                    "period": f"{year}-{month:02d}",
                    "total_bills": total_bills,
                    "total_revenue": float(total_revenue),
                    "collected_revenue": float(collected_revenue),
                    "pending_revenue": float(pending_revenue),
                    "average_bill": float(average_bill),
                    "min_bill": float(min_bill),
                    "max_bill": float(max_bill),
                    "payment_success_rate": round(payment_success_rate, 2)
                }
            
            return {
                "period": f"{year}-{month:02d}",
                "total_bills": 0,
                "total_revenue": 0,
                "collected_revenue": 0,
                "pending_revenue": 0,
                "average_bill": 0,
                "min_bill": 0,
                "max_bill": 0,
                "payment_success_rate": 0
            }
        
        except Exception as e:
            logger.error(f"Error generating revenue report: {e}")
            return {
                "period": f"{year}-{month:02d}",
                "error": str(e)
            }
    
    def get_consumption_analytics(self, customer_id: str = None) -> Dict:
        """
        Analyze consumption patterns
        
        Args:
            customer_id: Optional customer ID to filter by
        
        Returns:
            Dictionary with consumption metrics
        """
        logger.info(f"Analyzing consumption for customer: {customer_id or 'all'}")
        
        try:
            # Get consumption data from meter readings
            bills = self.db.supabase.table('bills').select('*')
            if customer_id:
                bills = bills.eq('customer_id', customer_id)
            
            result = bills.execute()
            
            if not result.data:
                return {
                    "total_consumption": 0,
                    "average_consumption": 0,
                    "peak_consumption": 0,
                    "low_consumption": 0,
                    "trend": "stable"
                }
            
            df = pd.DataFrame(result.data)
            
            total_consumption = df['consumption_kwh'].sum()
            avg_consumption = df['consumption_kwh'].mean()
            peak_consumption = df['consumption_kwh'].max()
            low_consumption = df['consumption_kwh'].min()
            
            # Calculate trend (simple: compare first and second half averages)
            mid_point = len(df) // 2
            if len(df) > 1:
                first_half_avg = df['consumption_kwh'].iloc[:mid_point].mean()
                second_half_avg = df['consumption_kwh'].iloc[mid_point:].mean()
                
                if second_half_avg > first_half_avg * 1.1:
                    trend = "increasing"
                elif second_half_avg < first_half_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            return {
                "customer_id": customer_id or "all_customers",
                "total_consumption": round(total_consumption, 2),
                "average_consumption": round(avg_consumption, 2),
                "peak_consumption": round(peak_consumption, 2),
                "low_consumption": round(low_consumption, 2),
                "trend": trend,
                "number_of_bills": len(df)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing consumption: {e}")
            return {"error": str(e)}
    
    def get_payment_success_rate(self, days: int = 30) -> Dict:
        """
        Calculate payment success rate over time period
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with payment metrics
        """
        logger.info(f"Calculating payment success rate for last {days} days")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = self.db.supabase.table('bills')\
                .select('status')\
                .gte('created_at', cutoff_date.isoformat())\
                .execute()
            
            if not result.data:
                return {
                    "period_days": days,
                    "total_bills": 0,
                    "paid_bills": 0,
                    "pending_bills": 0,
                    "overdue_bills": 0,
                    "success_rate": 0
                }
            
            df = pd.DataFrame(result.data)
            
            total_bills = len(df)
            paid_bills = len(df[df['status'] == 'paid'])
            paid_bills = len(df[df['status'] == 'paid'])
            pending_bills = len(df[df['status'].isin(['pending', 'generated', 'overdue'])])
            overdue_bills = len(df[df['status'] == 'overdue'])
            
            success_rate = (paid_bills / total_bills * 100) if total_bills > 0 else 0
            
            return {
                "period_days": days,
                "total_bills": total_bills,
                "paid_bills": paid_bills,
                "pending_bills": pending_bills,
                "overdue_bills": overdue_bills,
                "success_rate": round(success_rate, 2)
            }
        
        except Exception as e:
            logger.error(f"Error calculating payment success rate: {e}")
            return {"error": str(e)}
    
    def get_customer_segmentation(self) -> Dict:
        """
        Segment customers by consumption and payment behavior
        
        Returns:
            Dictionary with customer segments
        """
        logger.info("Analyzing customer segmentation")
        
        try:
            # Get all bills with customer info
            result = self.db.supabase.table('bills')\
                .select('customer_id, consumption_kwh, amount, status')\
                .execute()
            
            if not result.data:
                return {
                    "segments": {},
                    "total_customers": 0
                }
            
            df = pd.DataFrame(result.data)
            
            # Group by customer
            customer_summary = df.groupby('customer_id').agg({
                'consumption_kwh': 'mean',
                'amount': 'mean',
                'status': lambda x: (x == 'paid').sum() / len(x) * 100
            }).reset_index()
            
            customer_summary.columns = ['customer_id', 'avg_consumption', 'avg_bill', 'payment_rate']
            
            # Segment customers
            segments = {
                "high_value": [],  # High consumption, good payment
                "at_risk": [],     # High consumption, poor payment
                "loyal": [],       # Low consumption, good payment
                "low_engagement": []  # Low consumption, poor payment
            }
            
            consumption_median = customer_summary['avg_consumption'].median()
            
            for _, row in customer_summary.iterrows():
                customer = {
                    "customer_id": row['customer_id'],
                    "avg_consumption": round(row['avg_consumption'], 2),
                    "avg_bill": round(row['avg_bill'], 2),
                    "payment_rate": round(row['payment_rate'], 2)
                }
                
                if row['avg_consumption'] > consumption_median:
                    if row['payment_rate'] >= 70:
                        segments["high_value"].append(customer)
                    else:
                        segments["at_risk"].append(customer)
                else:
                    if row['payment_rate'] >= 70:
                        segments["loyal"].append(customer)
                    else:
                        segments["low_engagement"].append(customer)
            
            return {
                "segments": {
                    "high_value": {
                        "count": len(segments["high_value"]),
                        "customers": segments["high_value"][:5]  # Top 5
                    },
                    "at_risk": {
                        "count": len(segments["at_risk"]),
                        "customers": segments["at_risk"][:5]
                    },
                    "loyal": {
                        "count": len(segments["loyal"]),
                        "customers": segments["loyal"][:5]
                    },
                    "low_engagement": {
                        "count": len(segments["low_engagement"]),
                        "customers": segments["low_engagement"][:5]
                    }
                },
                "total_customers": len(customer_summary)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing customer segmentation: {e}")
            return {"error": str(e)}
    
    def get_revenue_trend(self, months: int = 6) -> List[Dict]:
        """
        Get revenue trend over multiple months
        
        Args:
            months: Number of months to analyze
        
        Returns:
            List of monthly revenue data
        """
        logger.info(f"Analyzing revenue trend for last {months} months")
        
        trend_data = []
        current_date = datetime.now()
        
        for i in range(months):
            month_date = current_date - timedelta(days=30 * i)
            report = self.get_monthly_revenue_report(month_date.year, month_date.month)
            trend_data.insert(0, report)
        
        return trend_data
