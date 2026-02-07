from sqlalchemy.orm import Session
from services.models.models import Role, User
from services.models.transaction_models import ServiceCategory, ServiceProvider, CommissionStructure
from services.auth.auth import get_password_hash
from database.database import SessionLocal, engine
import asyncio

async def create_initial_roles(db: Session):
    roles = [
        {"name": "superadmin", "description": "Super Administrator with full access"},
        {"name": "admin", "description": "Administrator with limited super admin access"},
        {"name": "whitelabel", "description": "White Label Partner"},
        {"name": "master_distributor", "description": "Master Distributor"},
        {"name": "distributor", "description": "Distributor"},
        {"name": "retailer", "description": "Retailer"},
        {"name": "customer", "description": "End Customer"}
    ]
    
    for role_data in roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()

async def create_superadmin(db: Session):
    # Check if superadmin exists
    superadmin = db.query(User).join(Role).filter(Role.name == "superadmin").first()
    if not superadmin:
        # Get superadmin role
        role = db.query(Role).filter(Role.name == "superadmin").first()
        if not role:
            print("Superadmin role not found. Please run create_initial_roles first.")
            return
        
        # Create superadmin user
        superadmin = User(
            username="superadmin",
            email="superadmin@bandarupay.pro",
            mobile="9999999999",
            first_name="Super",
            last_name="Admin",
            hashed_password=get_password_hash("superadmin@123"),
            hashed_pin=get_password_hash("123456"),
            role_id=role.id,
            is_active=True,
            is_verified=True
        )
        db.add(superadmin)
        db.commit()

async def create_service_categories(db: Session):
    categories = [
        {
            "name": "Mobile Recharge",
            "description": "Mobile prepaid and postpaid recharge services",
            "service_type": "mobile"
        },
        {
            "name": "DTH",
            "description": "DTH recharge services",
            "service_type": "dth"
        },
        {
            "name": "Electricity",
            "description": "Electricity bill payment services",
            "service_type": "electricity"
        },
        {
            "name": "Water",
            "description": "Water bill payment services",
            "service_type": "water"
        },
        {
            "name": "Gas",
            "description": "Gas bill payment services",
            "service_type": "gas"
        },
        {
            "name": "Broadband",
            "description": "Broadband bill payment services",
            "service_type": "broadband"
        },
        {
            "name": "Insurance",
            "description": "Insurance premium payment services",
            "service_type": "insurance"
        }
    ]
    
    for cat_data in categories:
        category = db.query(ServiceCategory).filter(
            ServiceCategory.name == cat_data["name"]
        ).first()
        if not category:
            category = ServiceCategory(**cat_data)
            db.add(category)
    
    db.commit()

async def create_initial_commission_structures(db: Session):
    # Get roles
    roles = db.query(Role).all()
    role_map = {role.name: role.id for role in roles}
    
    # Define base commission structures
    structures = [
        # Mobile Recharge
        {
            "role_name": "whitelabel",
            "commission_percentage": 2.5,
            "charge_percentage": 0.5,
            "min_amount": 10,
            "max_amount": 10000
        },
        {
            "role_name": "master_distributor",
            "commission_percentage": 2.0,
            "charge_percentage": 0.4,
            "min_amount": 10,
            "max_amount": 10000
        },
        {
            "role_name": "distributor",
            "commission_percentage": 1.5,
            "charge_percentage": 0.3,
            "min_amount": 10,
            "max_amount": 10000
        },
        {
            "role_name": "retailer",
            "commission_percentage": 1.0,
            "charge_percentage": 0.2,
            "min_amount": 10,
            "max_amount": 10000
        }
    ]
    
    # Get service categories
    categories = db.query(ServiceCategory).all()
    
    # Create commission structures for each role and service category
    for structure in structures:
        role_id = role_map.get(structure["role_name"])
        if not role_id:
            continue
            
        for category in categories:
            existing = db.query(CommissionStructure).filter(
                CommissionStructure.role_id == role_id,
                CommissionStructure.service_id == category.id
            ).first()
            
            if not existing:
                commission = CommissionStructure(
                    role_id=role_id,
                    service_id=category.id,
                    commission_percentage=structure["commission_percentage"],
                    charge_percentage=structure["charge_percentage"],
                    min_amount=structure["min_amount"],
                    max_amount=structure["max_amount"],
                    is_active=True
                )
                db.add(commission)
    
    db.commit()

async def main():
    db = SessionLocal()
    try:
        print("Creating initial roles...")
        await create_initial_roles(db)
        
        print("Creating superadmin user...")
        await create_superadmin(db)
        
        print("Creating service categories...")
        await create_service_categories(db)
        
        print("Creating initial commission structures...")
        await create_initial_commission_structures(db)
        
        print("Initial setup completed successfully!")
    
    except Exception as e:
        print(f"Error during setup: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
