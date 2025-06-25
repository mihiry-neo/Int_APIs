import httpx
from faker import Faker
import random
from tqdm import tqdm
 
fake = Faker()
url = "http://127.0.0.1:8000/users/register"  # Change this if your API is hosted elsewhere
 
genders = ["male", "female", "other"]
nationalities = ["Indian", "American", "British", "German", "French", "Japanese", "Canadian"]
 
def generate_user():
    password = fake.password(length=10)
    return {
        "username": fake.user_name(),
        "email": fake.unique.email(),
        "password": password,
        "gender": random.choice(genders),
        "age": random.randint(18, 65),
        "phone_number": fake.phone_number(),
        "nationality": random.choice(nationalities),
        "is_active": random.choice([True, False])
    }
 
def main():
    with httpx.Client(timeout=10) as client:
        for _ in tqdm(range(50000), desc="Creating users"):
            user_data = generate_user()
            try:
                response = client.post(url, json=user_data)
                if response.status_code != 200 and response.status_code != 201:
                    print(f"Failed: {response.status_code}, {response.text}")
            except Exception as e:
                print(f"Exception: {e}")
 
if __name__ == "__main__":
    main()