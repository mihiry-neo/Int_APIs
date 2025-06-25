from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import sys, os

# Path setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# DB and Routers
from database import SessionLocal, engine, Base, get_db
from Products.routes import router as products_router
from Orders.routes import order_router, cart_router
from Users.routes import router as users_router

# Models & Generator
from datagen import DataGenerator
from Users.models import User
from Products.models import Product, Category

# Load env and init
load_dotenv()
Base.metadata.create_all(bind=engine)
generator = DataGenerator()

app = FastAPI(description="FastAPI E-commerce Project")

# Routers
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(products_router, tags=["Products"])
app.include_router(order_router, tags=["Orders"])
app.include_router(cart_router, tags=["Cart"])

@app.post("/generate-data")
def generate_bulk_data(count: int = 100, db: Session = Depends(get_db)):
    try:
        created_users = generator.generate_random_users(count=min(count, 50), db=db)
        print(f"✅ Users created: {created_users}")

        if db.query(Category).count() == 0:
            categories = generator.create_categories(db)
        else:
            categories = db.query(Category).all()

        print(f"✅ Categories available: {len(categories)}")

        created_products = generator.create_products(db, categories=categories, count=count)
        print(f"✅ Products created: {created_products}")

        users = db.query(User).all()
        products = db.query(Product).all()
        print(f"🧾 Users in DB: {len(users)}, Products in DB: {len(products)}")

        if users and products:
            created_orders = generator.create_carts_and_orders(db, users, products, num_orders=count)
            print(f"✅ Orders created: {created_orders}")
        else:
            print("⚠️ Skipping order generation: No users or products found.")

        return {
            "message": f"✅ Successfully generated {count} records.",
            "users": len(users),
            "categories": len(categories),
            "products": len(products),
        }
    
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        db.close()

