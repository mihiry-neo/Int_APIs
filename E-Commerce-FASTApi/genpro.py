from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datagen import DataGenerator  # Assuming your provided code is saved as Products/generator.py
from database import Base
import sys

# Load .env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")

# Setup DB session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def main(product_count: int = 50):
    db = SessionLocal()
    generator = DataGenerator()

    print("🚀 Generating categories...")
    categories = generator.create_categories(db)
    if not categories:
        print("❌ Failed to generate categories. Aborting product generation.")
        return

    print(f"🚀 Generating {product_count} products...")
    products = generator.create_products(db, categories, product_count)

    print(f"✅ Successfully generated {len(products)} products.")

if __name__ == "__main__":
    # You can change the count here or accept CLI args
    main(product_count=2500)
