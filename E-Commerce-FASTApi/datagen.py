from faker import Faker
import random
from sqlalchemy.orm import Session
from Users.models import User
from auth import get_password_hash
from database import SessionLocal
from typing import List, Dict, Any
from Products.models import Product, Category, Inventory
from Orders.models import Cart, CartItem, Order, OrderStatus
from Products.crud import reserve_products, finalize_products
from datetime import datetime, timezone, timedelta
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def utc_now():
    return datetime.now(timezone.utc)

fake = Faker()

class DataGenerator:
    def __init__(self):
        self.faker = Faker()
        self.global_categories = [
            "Fashion", "Electronics", "Home & Garden", "Food & Beverage",
            "Health & Beauty", "Books & Media", "Toys & Games",
            "Sports & Outdoors", "DIY & Hardware", "Furniture"
        ]
        self.category_subcategories = {
            "Fashion": ["Clothing", "Footwear", "Accessories"],
            "Electronics": ["Mobiles", "Laptops", "Appliances"],
            "Home & Garden": ["Decor", "Plants", "Kitchen"],
            "Food & Beverage": ["Snacks", "Drinks", "Groceries"],
            "Health & Beauty": ["Skincare", "Supplements", "Makeup"],
            "Books & Media": ["Books", "Magazines", "E-books"],
            "Toys & Games": ["Board Games", "Action Figures", "Educational"],
            "Sports & Outdoors": ["Fitness", "Cycling", "Camping"],
            "DIY & Hardware": ["Tools", "Paint", "Electrical"],
            "Furniture": ["Bedroom", "Office", "Living Room"]
        }
        self.brand_names = [
            "Astra", "Zenex", "Nova", "UrbanMode", "GearPro",
            "CraftHaus", "NextEra", "Skyline", "PureEssence", "Flytek"
        ]

    def generate_random_users(self, count: int = 10, db: Session = SessionLocal()):
        genders = ["Male", "Female", "Other"]
        created = 0

        try:
            for _ in range(count):
                email = fake.unique.email()
                if db.query(User).filter_by(email=email).first():
                    continue

                new_user = User(
                    username=fake.user_name(),
                    email=email,
                    password=get_password_hash("StrongPassword123!"),
                    gender=random.choice(genders),
                    age=random.randint(18, 65),
                    phone_number=fake.phone_number()[:20],  # LIMIT LENGTH
                    nationality=fake.country(),
                    is_active=True
                )
                db.add(new_user)
                created += 1

            db.commit()
            print(f"✅ Created {created} random users directly in DB.")
            return created
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating users: {e}")
            return 0

    def create_categories(self, db: Session) -> List[Category]:
        categories = []
        try:
            for main_name in self.global_categories:
                main_cat = Category(name=main_name, parent_id=None)
                db.add(main_cat)
                db.flush()
                categories.append(main_cat)

                for sub in self.category_subcategories.get(main_name, []):
                    sub_cat = Category(name=f"{main_name} - {sub}", parent_id=main_cat.category_id)
                    db.add(sub_cat)
                    db.flush()
                    categories.append(sub_cat)

            db.commit()
            return categories
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating categories: {e}")
            return []

    def generate_brand(self) -> str:
        return random.choice([
            random.choice(self.brand_names),
            f"{self.faker.last_name()} {random.choice(['Inc', 'Corp', 'Ltd', 'Group'])}",
            f"{self.faker.country_code()} Tech",
            f"{self.faker.word().capitalize()}Works"
        ])

    def generate_product_attributes(self, category_name: str) -> Dict[str, Any]:
        return {
            "color": self.faker.color_name(),
            "weight": (
                f"{random.uniform(0.2, 3.0):.2f} kg"
                if "Electronics" in category_name or "Toys" in category_name
                else f"{random.uniform(5.0, 50.0):.2f} kg"
                if "Furniture" in category_name
                else f"{random.uniform(0.5, 10.0):.2f} kg"
            ),
            "material": (
                random.choice(["Cotton", "Polyester", "Denim", "Wool", "Silk"])
                if "Fashion" in category_name
                else random.choice(["Wood", "Metal", "Glass", "Plastic", "Leather"])
                if "Furniture" in category_name
                else random.choice(["Plastic", "Aluminum", "Glass"])
            ),
            "rating": round(random.uniform(3.0, 5.0), 1)
        }

    def create_products(self, db: Session, categories: List[Category], count: int) -> List[Product]:
        products = []
        categories_with_expiry = {"Food & Beverage", "Health & Beauty"}

        try:
            for _ in range(count):
                if not categories:
                    raise ValueError("No categories available.")

                category = random.choice(categories)
                stock_quantity = random.randint(0, 1000)

                product_data = {
                    "name": f"{self.faker.word().capitalize()} {self.faker.word().capitalize()}",
                    "price": round(
                        random.uniform(200.0, 2000.0)
                        if "Electronics" in category.name or "Furniture" in category.name
                        else random.uniform(50.0, 500.0)
                        if "Fashion" in category.name
                        else random.uniform(10.0, 300.0),
                        2
                    ),
                    "category_id": category.category_id,
                    "brand": self.generate_brand(),
                    "attributes": self.generate_product_attributes(category.name)
                }

                product = Product(**product_data)
                db.add(product)
                db.flush()

                expiry_date = (
                    datetime.now() + timedelta(days=random.randint(30, 365))
                    if category.name in categories_with_expiry else datetime(9999, 12, 31)
                )

                inventory = Inventory(
                    product_id=product.product_id,
                    quantity_available=stock_quantity,
                    quantity_reserve=random.randint(0, min(50, stock_quantity // 4)),
                    reorder_level=random.randint(5, 25),
                    reorder_quantity=random.randint(20, 100),
                    unit_cost=round(product_data["price"] * random.uniform(0.4, 0.7), 2),
                    last_restocked=datetime.now() - timedelta(days=random.randint(1, 30)),
                    expiry_date=expiry_date,
                    batch_number=self.faker.uuid4(),
                    location=self.faker.city()
                )
                db.add(inventory)

                products.append(product)

            db.commit()
            print(f"✅ Created {len(products)} products.")
            return products
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating products: {e}")
            return []

    def create_carts_and_orders(self, db: Session, users: list[User], products: list[Product], num_orders: int = 100):
        created_orders = 0

        for _ in range(num_orders):
            user = random.choice(users)
            cart = Cart(user_id=user.user_id, created_at=utc_now())
            db.add(cart)
            db.flush()

            selected_products = random.sample(products, k=min(random.randint(1, 5), len(products)))
            order_items = []
            total_amount = 0.0
            failed = False

            for product in selected_products:
                quantity = random.randint(1, 3)

                if not reserve_products(db, product_id=product.product_id, quantity=quantity):
                    failed = True
                    break

                cart_item = CartItem(
                    cart_id=cart.cart_id,
                    product_id=product.product_id,
                    quantity=quantity
                )
                db.add(cart_item)

                order_items.append({
                    "product_id": product.product_id,
                    "name": product.name,
                    "qty": quantity,
                    "price": float(product.price)
                })
                total_amount += float(product.price) * quantity

            if failed or not order_items:
                db.rollback()
                continue

            order = Order(
                user_id=user.user_id,
                order_date=utc_now(),
                items=order_items,
                total_amount=round(total_amount, 2),
                status=OrderStatus.pending,
                payment_method=random.choice(["credit_card", "paypal", "stripe"]),
                shipping_address=fake.address()
            )
            db.add(order)

            finalize_products(db, order)
            created_orders += 1

        db.commit()
        print(f"✅ Created {created_orders} valid orders from carts.")
        return created_orders
