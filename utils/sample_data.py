"""
Sample data generator for testing the billing system
Creates realistic meter readings for testing
"""

from datetime import datetime, timedelta
import random


class SampleDataGenerator:
    """Generate sample data for testing"""
    
    @staticmethod
    def generate_meter_readings(
        meter_id: str = "METER001",
        customer_id: str = "CUST001",
        num_months: int = 12,
        base_consumption: float = 200.0,
        variance: float = 50.0
    ):
        """
        Generate historical meter readings
        
        Args:
            meter_id: Meter identifier
            customer_id: Customer identifier
            num_months: Number of months of data to generate
            base_consumption: Base monthly consumption in kWh
            variance: Random variance in consumption
        
        Returns:
            List of meter reading records
        """
        readings = []
        current_date = datetime.now()
        current_reading = 1000.0  # Starting meter reading
        
        for i in range(num_months, 0, -1):
            # Calculate reading date (1st of each month)
            reading_date = current_date - timedelta(days=30 * i)
            reading_date = reading_date.replace(day=1)
            
            # Add consumption with random variance
            consumption = base_consumption + random.uniform(-variance, variance)
            current_reading += consumption
            
            readings.append({
                "meter_id": meter_id,
                "customer_id": customer_id,
                "reading_value": round(current_reading, 2),
                "reading_date": reading_date.strftime("%Y-%m-%d"),
                "created_at": reading_date.isoformat()
            })
        
        return readings
    
    @staticmethod
    def generate_test_request(
        meter_id: str = "METER001",
        customer_id: str = "CUST001",
        customer_phone: str = "+919876543210",
        previous_reading: float = 3992.0,
        consumption: float = 150.0,
        connected_load_kw: float = 7.0,
        tariff_type: str = "residential"
    ):
        """
        Generate a test API request
        
        Returns:
            Dict formatted as API request payload
        """
        current_reading = previous_reading + consumption
        
        return {
            "user_id": "auth0|test123456789",
            "meter_id": meter_id,
            "customer_id": customer_id,
            "customer_phone": customer_phone,
            "reading_value": current_reading,
            "reading_date": datetime.now().strftime("%Y-%m-%d"),
            "connected_load_kw": connected_load_kw,
            "tariff_type": tariff_type
        }
    
    @staticmethod
    def generate_sql_inserts(readings: list) -> str:
        """Generate SQL INSERT statements for meter readings"""
        sql_statements = []
        
        for reading in readings:
            sql = f"""INSERT INTO meter_readings (meter_id, customer_id, reading_value, reading_date, created_at)
VALUES ('{reading['meter_id']}', '{reading['customer_id']}', {reading['reading_value']}, '{reading['reading_date']}', '{reading['created_at']}');"""
            sql_statements.append(sql)
        
        return "\n".join(sql_statements)


# Example usage
if __name__ == "__main__":
    generator = SampleDataGenerator()
    
    # Generate 12 months of readings
    print("Generating sample meter readings...")
    print("=" * 70)
    
    readings = generator.generate_meter_readings(
        meter_id="METER001",
        customer_id="CUST001",
        num_months=12,
        base_consumption=200.0,
        variance=50.0
    )
    
    print(f"\nGenerated {len(readings)} meter readings:")
    for reading in readings[-3:]:  # Show last 3
        print(f"  {reading['reading_date']}: {reading['reading_value']} kWh")
    
    print("\n" + "=" * 70)
    print("\nSQL INSERT Statements:")
    print("=" * 70)
    print(generator.generate_sql_inserts(readings))
    
    print("\n" + "=" * 70)
    print("\nSample API Request:")
    print("=" * 70)
    import json
    test_request = generator.generate_test_request(
        previous_reading=readings[-1]['reading_value']
    )
    print(json.dumps(test_request, indent=2))
