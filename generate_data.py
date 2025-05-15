import csv
import random
from datetime import datetime, timedelta

# === Configurable Parameters ===
TOTAL_USERS = 5000
TOTAL_PRODUCTS = 1000
TOTAL_ORDERS = 50000
TOTAL_REVIEWS = 10000

# === Generate CSV for Users ===
with open('users.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['name', 'age', 'city', 'signup_date'])  # Header
    for i in range(1, TOTAL_USERS + 1):
        name = f'User_{i}'
        age = random.randint(18, 60)
        city = random.choice(['New York', 'London', 'Tokyo', 'Delhi', 'Berlin'])
        signup_date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))
        writer.writerow([name, age, city, signup_date])

# === Generate CSV for Products ===
categories = ['Laptops', 'Mobiles', 'Tablets', 'Accessories', 'Desktops', 'Wearables']
brands = ['Apple', 'Samsung', 'Dell', 'HP', 'Lenovo', 'Asus', 'Sony', 'Acer']
with open('products.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['name', 'category', 'price', 'brand', 'rating'])  # Header
    for i in range(1, TOTAL_PRODUCTS + 1):
        name = f'Product_{i}'
        category = random.choice(categories)
        price = round(random.uniform(100, 2000), 2)
        brand = random.choice(brands)
        rating = round(random.uniform(2.5, 5.0), 2)
        writer.writerow([name, category, price, brand, rating])

# === Generate CSV for Seasons ===
seasons = [
    ('College Start', '2024-07-01', '2024-09-01'),
    ('Holiday Sale', '2024-12-01', '2024-12-31'),
    ('Back to School', '2024-08-01', '2024-09-15'),
    ('Summer Sale', '2024-06-01', '2024-06-30'),
    ('New Year', '2025-01-01', '2025-01-10'),
]
with open('seasons.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['name', 'start_date', 'end_date'])  # Header
    for name, start, end in seasons:
        writer.writerow([name, start, end])

# === Generate CSV for Promotions ===
with open('promotions.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['product_id', 'season_id', 'discount_percent'])  # Header
    for _ in range(100):
        product_id = random.randint(1, TOTAL_PRODUCTS)
        season_id = random.randint(1, len(seasons))
        discount = random.choice([10, 15, 20, 25, 30])
        writer.writerow([product_id, season_id, discount])

# === Generate CSV for Orders ===
with open('orders.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['user_id', 'product_id', 'order_date', 'status', 'quantity'])  # Header
    for i in range(TOTAL_ORDERS):
        user_id = random.randint(1, TOTAL_USERS)
        product_id = random.randint(1, TOTAL_PRODUCTS)
        order_date = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 900))
        status = random.choice(['delivered', 'pending', 'cancelled'])
        quantity = random.randint(1, 5)
        writer.writerow([user_id, product_id, order_date, status, quantity])

# === Generate CSV for Reviews ===
with open('reviews.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['user_id', 'product_id', 'rating', 'review_date', 'text'])  # Header
    for i in range(TOTAL_REVIEWS):
        user_id = random.randint(1, TOTAL_USERS)
        product_id = random.randint(1, TOTAL_PRODUCTS)  # Ensure this matches the range in products
        rating = round(random.uniform(2.5, 5.0), 2)
        review_date = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 900))
        text = f"Review {i} for product {product_id}"
        writer.writerow([user_id, product_id, rating, review_date, text])
