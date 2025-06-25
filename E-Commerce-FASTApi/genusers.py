import asyncio
import httpx
from faker import Faker
import random
from tqdm.asyncio import tqdm_asyncio
 
fake = Faker()
url = "http://127.0.0.1:8000/users/register"
 
genders = ["male", "female", "other"]
nationalities = ["Indian", "American", "British", "German", "French", "Japanese", "Canadian"]
 
def generate_user():
    return {
        "username": fake.user_name(),
        "email": fake.unique.email(),
        "password": fake.password(length=10),
        "gender": random.choice(genders),
        "age": random.randint(18, 65),
        "phone_number": fake.phone_number(),
        "nationality": random.choice(nationalities),
        "is_active": random.choice([True, False])
    }
 
async def post_user(client: httpx.AsyncClient, user_data: dict):
    try:
        await client.post(url, json=user_data)
    except:
        pass  # Silent failure
 
async def main():
    total_users = 50000
    batch_size = 1000  # Number of concurrent requests per batch
 
    async with httpx.AsyncClient(timeout=10) as client:
        for i in tqdm_asyncio(range(0, total_users, batch_size), desc="Creating users"):
            tasks = [
                post_user(client, generate_user())
                for _ in range(min(batch_size, total_users - i))
            ]
            await asyncio.gather(*tasks)
 
if __name__ == "__main__":
    asyncio.run(main())
 