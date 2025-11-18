"""
Synthetic tariff rules based on residential billing structure
"""

class TariffRules:
    """Synthetic tariff rules for electricity billing"""
    
    # Standard residential tariff structure
    RESIDENTIAL_STANDARD = {
        "id": "TARIFF_RES_001",
        "name": "Residential Standard Tariff",
        "active": True,
        "currency": "INR",
        "billing_cycle": "monthly",
        
        # Fixed charges
        "fixed_charges": {
            "motor_charges": 12.00,
            "common_area_maintenance": 2954.00,
            "grid_charges_per_kw": 51.00  # Rs.51/kW
        },
        
        # Energy charges - tiered pricing
        "energy_tiers": [
            {
                "tier": "Tier 1 (0-100 kWh)",
                "min_kwh": 0,
                "max_kwh": 100,
                "rate": 4.50
            },
            {
                "tier": "Tier 2 (101-300 kWh)",
                "min_kwh": 101,
                "max_kwh": 300,
                "rate": 6.00
            },
            {
                "tier": "Tier 3 (301-500 kWh)",
                "min_kwh": 301,
                "max_kwh": 500,
                "rate": 7.50
            },
            {
                "tier": "Tier 4 (500+ kWh)",
                "min_kwh": 501,
                "max_kwh": float('inf'),
                "rate": 9.00
            }
        ],
        
        # Taxes and additional charges
        "taxes": {
            "electricity_duty": 0.10,  # 10% of energy charges
            "tax_on_sale": 0.00  # 0% for now
        },
        
        # Payment terms
        "payment_terms": {
            "due_days": 15,
            "bounce_charge": 500.00,
            "late_payment_interest_rate": 0.18  # 18% per annum
        }
    }
    
    # Commercial tariff structure
    COMMERCIAL_STANDARD = {
        "id": "TARIFF_COM_001",
        "name": "Commercial Standard Tariff",
        "active": True,
        "currency": "INR",
        "billing_cycle": "monthly",
        
        "fixed_charges": {
            "motor_charges": 20.00,
            "common_area_maintenance": 5000.00,
            "grid_charges_per_kw": 75.00
        },
        
        "energy_tiers": [
            {
                "tier": "Tier 1 (0-200 kWh)",
                "min_kwh": 0,
                "max_kwh": 200,
                "rate": 7.00
            },
            {
                "tier": "Tier 2 (201-500 kWh)",
                "min_kwh": 201,
                "max_kwh": 500,
                "rate": 8.50
            },
            {
                "tier": "Tier 3 (500+ kWh)",
                "min_kwh": 501,
                "max_kwh": float('inf'),
                "rate": 10.00
            }
        ],
        
        "taxes": {
            "electricity_duty": 0.12,
            "tax_on_sale": 0.05
        },
        
        "payment_terms": {
            "due_days": 15,
            "bounce_charge": 1000.00,
            "late_payment_interest_rate": 0.18
        }
    }
    
    @classmethod
    def get_tariff_by_type(cls, tariff_type: str = "residential"):
        """Get tariff rules by type"""
        if tariff_type.lower() == "commercial":
            return cls.COMMERCIAL_STANDARD
        return cls.RESIDENTIAL_STANDARD
    
    @classmethod
    def get_all_active_tariffs(cls):
        """Get all active tariff rules"""
        return [
            cls.RESIDENTIAL_STANDARD,
            cls.COMMERCIAL_STANDARD
        ]
    
    @classmethod
    def calculate_energy_charges(cls, consumption_kwh: float, tariff_type: str = "residential"):
        """
        Calculate energy charges based on tiered pricing
        
        Args:
            consumption_kwh: Total consumption in kWh
            tariff_type: Type of tariff (residential/commercial)
        
        Returns:
            dict with tier breakdown and total
        """
        tariff = cls.get_tariff_by_type(tariff_type)
        tiers = tariff["energy_tiers"]
        
        tier_breakdown = []
        remaining_kwh = consumption_kwh
        total_energy_charge = 0.0
        
        for tier in tiers:
            if remaining_kwh <= 0:
                break
            
            # Calculate kWh in this tier
            tier_min = tier["min_kwh"]
            tier_max = tier["max_kwh"]
            tier_capacity = tier_max - tier_min + 1 if tier_max != float('inf') else float('inf')
            
            kwh_in_tier = min(remaining_kwh, tier_capacity)
            tier_amount = kwh_in_tier * tier["rate"]
            
            tier_breakdown.append({
                "tier": tier["tier"],
                "kwh": round(kwh_in_tier, 2),
                "rate": tier["rate"],
                "amount": round(tier_amount, 2)
            })
            
            total_energy_charge += tier_amount
            remaining_kwh -= kwh_in_tier
        
        return {
            "tier_breakdown": tier_breakdown,
            "total_energy_charge": round(total_energy_charge, 2)
        }
    
    @classmethod
    def calculate_total_bill(
        cls,
        consumption_kwh: float,
        connected_load_kw: float = 7.0,
        tariff_type: str = "residential",
        previous_outstanding: float = 0.0
    ):
        """
        Calculate complete bill amount
        
        Args:
            consumption_kwh: Total consumption in kWh
            connected_load_kw: Connected load in kW
            tariff_type: Type of tariff
            previous_outstanding: Previous outstanding amount
        
        Returns:
            Complete bill breakdown
        """
        tariff = cls.get_tariff_by_type(tariff_type)
        
        # Energy charges
        energy_calc = cls.calculate_energy_charges(consumption_kwh, tariff_type)
        energy_charges = energy_calc["total_energy_charge"]
        
        # Fixed charges
        motor_charges = tariff["fixed_charges"]["motor_charges"]
        grid_charges = connected_load_kw * tariff["fixed_charges"]["grid_charges_per_kw"]
        common_area_charges = tariff["fixed_charges"]["common_area_maintenance"]
        
        # Subtotal before taxes
        subtotal = energy_charges + motor_charges + grid_charges + common_area_charges
        
        # Taxes
        electricity_duty = energy_charges * tariff["taxes"]["electricity_duty"]
        tax_on_sale = subtotal * tariff["taxes"].get("tax_on_sale", 0)
        
        # Total charges
        total_charges = subtotal + electricity_duty + tax_on_sale
        
        # Amount payable
        amount_payable = total_charges + previous_outstanding
        
        return {
            "consumption_kwh": round(consumption_kwh, 2),
            "connected_load_kw": connected_load_kw,
            "tariff_type": tariff_type,
            "tariff_name": tariff["name"],
            
            # Energy charges breakdown
            "energy_charges": {
                "tier_breakdown": energy_calc["tier_breakdown"],
                "total": round(energy_charges, 2)
            },
            
            # Fixed charges
            "fixed_charges": {
                "motor_charges": round(motor_charges, 2),
                "grid_charges": round(grid_charges, 2),
                "common_area_maintenance": round(common_area_charges, 2),
                "total": round(motor_charges + grid_charges + common_area_charges, 2)
            },
            
            # Taxes
            "taxes": {
                "electricity_duty": round(electricity_duty, 2),
                "tax_on_sale": round(tax_on_sale, 2),
                "total": round(electricity_duty + tax_on_sale, 2)
            },
            
            # Totals
            "subtotal": round(subtotal, 2),
            "total_charges": round(total_charges, 2),
            "previous_outstanding": round(previous_outstanding, 2),
            "amount_payable": round(amount_payable, 2),
            
            "currency": tariff["currency"],
            "payment_terms": tariff["payment_terms"]
        }


# Sample usage and testing
if __name__ == "__main__":
    # Example: Calculate bill for the provided bill image
    # Previous reading: 3992, Current reading: 3992 (0 consumption shown)
    # But bill shows charges, so using synthetic data
    
    print("Residential Bill Calculation Example:")
    print("=" * 60)
    
    bill = TariffRules.calculate_total_bill(
        consumption_kwh=0,  # As shown in the bill (3992 - 3992)
        connected_load_kw=7.0,  # 7KW from bill
        tariff_type="residential",
        previous_outstanding=0.0
    )
    
    import json
    print(json.dumps(bill, indent=2))
