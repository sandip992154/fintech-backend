"""
Sample data and initialization scripts for Scheme and Commission Management
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from services.models.scheme_models import (
    Scheme, ServiceOperator, Commission, CommissionSlab,
    ServiceTypeEnum, CommissionTypeEnum
)
from services.models.models import User, Role


def create_sample_operators(db: Session):
    """Create sample service operators"""
    
    operators_data = [
        # Mobile Recharge Operators
        {"name": "Airtel", "service_type": ServiceTypeEnum.MOBILE_RECHARGE},
        {"name": "Jio", "service_type": ServiceTypeEnum.MOBILE_RECHARGE},
        {"name": "VI", "service_type": ServiceTypeEnum.MOBILE_RECHARGE},
        {"name": "BSNL TOPUP", "service_type": ServiceTypeEnum.MOBILE_RECHARGE},
        {"name": "BSNL VALIDITY", "service_type": ServiceTypeEnum.MOBILE_RECHARGE},
        
        # DTH Recharge Operators
        {"name": "Tata Sky", "service_type": ServiceTypeEnum.DTH_RECHARGE},
        {"name": "Airtel Digital TV", "service_type": ServiceTypeEnum.DTH_RECHARGE},
        {"name": "Dish TV", "service_type": ServiceTypeEnum.DTH_RECHARGE},
        {"name": "Sun Direct", "service_type": ServiceTypeEnum.DTH_RECHARGE},
        
        # Bill Payment Operators
        {"name": "Electricity", "service_type": ServiceTypeEnum.BILL_PAYMENTS},
        {"name": "Water Bill", "service_type": ServiceTypeEnum.BILL_PAYMENTS},
        {"name": "Gas Bill", "service_type": ServiceTypeEnum.BILL_PAYMENTS},
        {"name": "Broadband", "service_type": ServiceTypeEnum.BILL_PAYMENTS},
        
        # AEPS Operators
        {"name": "ICICI AEPS", "service_type": ServiceTypeEnum.AEPS},
        {"name": "SBI AEPS", "service_type": ServiceTypeEnum.AEPS},
        {"name": "HDFC AEPS", "service_type": ServiceTypeEnum.AEPS},
        
        # DMT Operators
        {"name": "DMT Agent 1", "service_type": ServiceTypeEnum.DMT},
        {"name": "DMT Agent 2", "service_type": ServiceTypeEnum.DMT},
        
        # Micro ATM Operators
        {"name": "Micro ATM Service A", "service_type": ServiceTypeEnum.MICRO_ATM},
        {"name": "Micro ATM Service B", "service_type": ServiceTypeEnum.MICRO_ATM}
    ]
    
    for operator_data in operators_data:
        # Check if operator already exists
        existing = db.query(ServiceOperator).filter(
            ServiceOperator.name == operator_data["name"],
            ServiceOperator.service_type == operator_data["service_type"]
        ).first()
        
        if not existing:
            operator = ServiceOperator(**operator_data)
            db.add(operator)
    
    db.commit()


def create_sample_schemes(db: Session):
    """Create sample schemes"""
    
    # Get superadmin user
    superadmin = db.query(User).join(Role).filter(Role.name == "super_admin").first()
    if not superadmin:
        print("Warning: No superadmin user found. Skipping scheme creation.")
        return
    
    schemes_data = [
        {
            "name": "Default",
            "description": "Default commission scheme for all services",
            "created_by": superadmin.id
        },
        {
            "name": "Premium",
            "description": "Premium commission scheme with higher rates",
            "created_by": superadmin.id
        },
        {
            "name": "Test Scheme",
            "description": "Test scheme for development and testing",
            "created_by": superadmin.id
        }
    ]
    
    for scheme_data in schemes_data:
        # Check if scheme already exists
        existing = db.query(Scheme).filter(Scheme.name == scheme_data["name"]).first()
        
        if not existing:
            scheme = Scheme(**scheme_data)
            db.add(scheme)
    
    db.commit()


def create_sample_commissions(db: Session):
    """Create sample commission structures"""
    
    # Get default scheme
    default_scheme = db.query(Scheme).filter(Scheme.name == "Default").first()
    if not default_scheme:
        print("Warning: Default scheme not found. Skipping commission creation.")
        return
    
    # Mobile Recharge Commissions
    mobile_operators = db.query(ServiceOperator).filter(
        ServiceOperator.service_type == ServiceTypeEnum.MOBILE_RECHARGE
    ).all()
    
    mobile_commissions = [
        {
            "operator_name": "Airtel",
            "commission_type": CommissionTypeEnum.PERCENT,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 2.5,
            "masterdistributor": 2.3,
            "distributor": 2.1,
            "retailer": 2.0,
            "customer": 0.0
        },
        {
            "operator_name": "Jio",
            "commission_type": CommissionTypeEnum.PERCENT,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 1.1,
            "masterdistributor": 1.02,
            "distributor": 1.01,
            "retailer": 1.0,
            "customer": 0.0
        },
        {
            "operator_name": "VI",
            "commission_type": CommissionTypeEnum.PERCENT,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 3.5,
            "masterdistributor": 3.0,
            "distributor": 2.5,
            "retailer": 2.0,
            "customer": 0.0
        },
        {
            "operator_name": "BSNL TOPUP",
            "commission_type": CommissionTypeEnum.PERCENT,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 3.5,
            "masterdistributor": 3.0,
            "distributor": 2.5,
            "retailer": 2.0,
            "customer": 0.0
        },
        {
            "operator_name": "BSNL VALIDITY",
            "commission_type": CommissionTypeEnum.PERCENT,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 3.5,
            "masterdistributor": 3.0,
            "distributor": 2.5,
            "retailer": 2.0,
            "customer": 0.0
        }
    ]
    
    for comm_data in mobile_commissions:
        operator = next((op for op in mobile_operators if op.name == comm_data["operator_name"]), None)
        if operator:
            # Check if commission already exists
            existing = db.query(Commission).filter(
                Commission.scheme_id == default_scheme.id,
                Commission.operator_id == operator.id,
                Commission.service_type == ServiceTypeEnum.MOBILE_RECHARGE
            ).first()
            
            if not existing:
                commission = Commission(
                    scheme_id=default_scheme.id,
                    operator_id=operator.id,
                    service_type=ServiceTypeEnum.MOBILE_RECHARGE,
                    commission_type=comm_data["commission_type"],
                    superadmin=comm_data["superadmin"],
                    admin=comm_data["admin"],
                    whitelabel=comm_data["whitelabel"],
                    masterdistributor=comm_data["masterdistributor"],
                    distributor=comm_data["distributor"],
                    retailer=comm_data["retailer"],
                    customer=comm_data["customer"]
                )
                db.add(commission)
    
    # AEPS Commissions with Slabs
    aeps_operators = db.query(ServiceOperator).filter(
        ServiceOperator.service_type == ServiceTypeEnum.AEPS
    ).all()
    
    aeps_slabs = [
        {
            "slab_min": 0,
            "slab_max": 1000,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 0.35,
            "masterdistributor": 0.34,
            "distributor": 0.33,
            "retailer": 0.32,
            "customer": 0.0
        },
        {
            "slab_min": 1001,
            "slab_max": 5000,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 0.30,
            "masterdistributor": 0.29,
            "distributor": 0.28,
            "retailer": 0.27,
            "customer": 0.0
        },
        {
            "slab_min": 5001,
            "slab_max": 10000,
            "superadmin": 0.0,
            "admin": 0.0,
            "whitelabel": 0.25,
            "masterdistributor": 0.24,
            "distributor": 0.23,
            "retailer": 0.22,
            "customer": 0.0
        }
    ]
    
    for operator in aeps_operators:
        # Check if commission already exists
        existing = db.query(Commission).filter(
            Commission.scheme_id == default_scheme.id,
            Commission.operator_id == operator.id,
            Commission.service_type == ServiceTypeEnum.AEPS
        ).first()
        
        if not existing:
            commission = Commission(
                scheme_id=default_scheme.id,
                operator_id=operator.id,
                service_type=ServiceTypeEnum.AEPS,
                commission_type=CommissionTypeEnum.PERCENT
            )
            db.add(commission)
            db.flush()  # To get commission.id
            
            # Add slabs
            for slab_data in aeps_slabs:
                slab = CommissionSlab(
                    commission_id=commission.id,
                    **slab_data
                )
                db.add(slab)
    
    db.commit()


def initialize_scheme_management(db: Session):
    """Initialize complete scheme management system with sample data"""
    
    print("Initializing Scheme Management System...")
    
    try:
        # Create sample operators
        print("Creating service operators...")
        create_sample_operators(db)
        
        # Create sample schemes
        print("Creating sample schemes...")
        create_sample_schemes(db)
        
        # Create sample commissions
        print("Creating sample commissions...")
        create_sample_commissions(db)
        
        print("✅ Scheme Management System initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing Scheme Management System: {str(e)}")
        db.rollback()
        raise


if __name__ == "__main__":
    # This can be run as a standalone script
    from database.database import SessionLocal
    
    db = SessionLocal()
    try:
        initialize_scheme_management(db)
    finally:
        db.close()