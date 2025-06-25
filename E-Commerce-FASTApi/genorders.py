import random
from datetime import datetime, timezone
from faker import Faker
 
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from Users.models import User
from Products.models import Product, Inventory
 
fake = Faker()
client = TestClient(app)
 
TOTAL_CART_ITEMS_TO_INSERT = 1
NUM_ORDERS_TO_GENERATE = 500  # You can keep this fixed
used_product_ids = set()
 
 
def get_random_users(db, limit=10):
    return db.query(User).filter(User.is_active == True).limit(limit).all()
 
 
def get_products_with_stock(db):
    return (
        db.query(Product)
        .join(Inventory)
        .filter(Inventory.quantity_available > 0)
        .all()
    )
 
 
def create_cart_and_add_items(user_id, remaining_items, products):
    # Create one cart
    cart_resp = client.post("/cart/", json={"user_id": user_id})
    if cart_resp.status_code != 201:
        print(f"❌ Failed to create cart for user {user_id}")
        return 0
 
    cart_id = cart_resp.json()["cart_id"]
    items_added = 0
 
    for product in products:
        if product.product_id in used_product_ids:
            continue
        quantity = min(5, product.inventory.quantity_available)
        if quantity <= 0:
            continue
 
        payload = {
            "user_id": user_id,
            "product_id": product.product_id,
            "quantity": random.randint(1, quantity),
            "price": float(product.price)
        }
 
        res = client.post(f"/cart/{cart_id}/items", json=payload)
        if res.status_code in [200, 201]:
            print(f"✅ Added to cart: {res.json()}")
            used_product_ids.add(product.product_id)
            items_added += 1
        else:
            print(f"❌ Failed to add item: {res.json()}")
 
        if items_added >= remaining_items:
            break
 
    return items_added
 
 
def create_order_from_products(user_id, products):
    items = []
    for product in products:
        if product.inventory.quantity_available <= 0:
            continue
        quantity = random.randint(1, min(5, product.inventory.quantity_available))
        items.append({
            "product_id": product.product_id,
            "quantity": quantity,
            "price": float(product.price)
        })
 
    if not items:
        print(f"⚠️ No valid items to create order for user {user_id}")
        return None
 
    payload = {
        "user_id": user_id,
        "items": items,
        "payment_method": random.choice(["Credit Card", "PayPal", "Cash on Delivery"]),
        "shipping_address": fake.address().replace("\n", ", ")
    }
 
    response = client.post("/orders/", json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Order created for user {user_id}")
    else:
        print(f"❌ Order failed: {response.json()}")
    return response
 
 
def main():
    db = SessionLocal()
    try:
        users = get_random_users(db)
        if not users:
            print("❌ No active users found.")
            return
 
        products = get_products_with_stock(db)
        if not products:
            print("❌ No products with stock.")
            return
 
        print(f"🛒 Inserting exactly {TOTAL_CART_ITEMS_TO_INSERT} cart items...")
        total_inserted_items = 0
 
        while total_inserted_items < TOTAL_CART_ITEMS_TO_INSERT:
            user = random.choice(users)
            available_products = [
                p for p in get_products_with_stock(db)
                if p.product_id not in used_product_ids
            ]
            if not available_products:
                print("⚠️ No more unique products available.")
                break
 
            # Create a cart and insert as many as needed up to the remaining count
            items_to_add = TOTAL_CART_ITEMS_TO_INSERT - total_inserted_items
            selected_products = random.sample(
                available_products, min(len(available_products), items_to_add)
            )
 
            added = create_cart_and_add_items(user.user_id, items_to_add, selected_products)
            total_inserted_items += added
 
        print(f"✅ Finished adding exactly {total_inserted_items} cart items.\n")
 
        print(f"📦 Generating {NUM_ORDERS_TO_GENERATE} orders...")
        for _ in range(NUM_ORDERS_TO_GENERATE):
            user = random.choice(users)
            available_products = [
                p for p in get_products_with_stock(db)
                if p.product_id not in used_product_ids
            ]
            if len(available_products) < 3:
                break
            selected_products = random.sample(available_products, min(5, len(available_products)))
            create_order_from_products(user.user_id, selected_products)
 
        print("🎉 Script complete.")
    finally:
        db.close()
 
 
if __name__ == "__main__":
    main()
 