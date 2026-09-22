import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker


# -----------------------------
# Настройки генерации
# -----------------------------

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

fake = Faker("ru_RU")
fake.seed_instance(SEED)

N_USERS = 50_000

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 6, 30, 23, 59, 59)


# -----------------------------
# Генерация пользователей
# -----------------------------
def generate_users(n_users: int) -> pd.DataFrame:
    devices = ["mobile", "desktop", "tablet"]

    traffic_sources = [
        "organic",
        "paid_search",
        "social",
        "email",
        "direct",
        "referral"
    ]

    countries = [
        "Russia",
        "Kazakhstan",
        "Belarus",
        "Armenia",
        "Georgia"
    ]

    rows = []

    for user_id in range(1, n_users + 1):
        registration_date = fake.date_between(
            start_date=START_DATE.date(),
            end_date=END_DATE.date()
        )

        rows.append({
	    "experiment_group": random.choice(["control", "test"]),
            "user_id": user_id,
            "registration_date": registration_date,
            "country": random.choices(
                countries,
                weights=[70, 10, 8, 6, 6],
                k=1
            )[0],
            "device": random.choices(
                devices,
                weights=[60, 30, 10],
                k=1
            )[0],
            "traffic_source": random.choices(
                traffic_sources,
                weights=[30, 20, 15, 10, 15, 10],
                k=1
            )[0]
        })

    return pd.DataFrame(rows)


def generate_products() -> pd.DataFrame:
    categories = [
        "electronics",
        "home",
        "clothing",
        "beauty",
        "sports",
        "books",
        "accessories"
    ]

    price_ranges = {
        "electronics": (5000, 150000),
        "home": (1000, 50000),
        "clothing": (1000, 25000),
        "beauty": (500, 15000),
        "sports": (1000, 40000),
        "books": (300, 5000),
        "accessories": (500, 20000)
    }

    rows = []

    for product_id in range(1, 501):
        category = random.choice(categories)
        min_price, max_price = price_ranges[category]

        rows.append({
            "product_id": product_id,
            "category": category,
            "price": round(
                random.uniform(min_price, max_price),
                2
            )
        })

    return pd.DataFrame(rows)

def generate_events(users: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    event_id = 1

    product_ids = products["product_id"].tolist()

    for _, user in users.iterrows():

        registration = pd.Timestamp(user["registration_date"])

        # Не каждый зарегистрированный пользователь становится активным
        if random.random() < 0.20:
            continue

        # Первая сессия обычно происходит вскоре после регистрации
        first_session_delay = random.choices(
            population=[0, 1, 3, 7, 14],
            weights=[20, 25, 25, 20, 10],
            k=1
        )[0]

        first_session = registration + timedelta(
            days=first_session_delay,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        if first_session > END_DATE:
            continue

        session_starts = [first_session]

        # Генерируем последующие возвращения.
        # Чем дальше от предыдущей активности,
        # тем ниже вероятность следующей сессии.
        current_session = first_session

        while True:

            days_since_registration = (
                current_session - registration
            ).days

            if days_since_registration >= 150:
                break

            # Базовая вероятность следующего возвращения
            if days_since_registration <= 7:
                return_probability = 0.55
            elif days_since_registration <= 30:
                return_probability = 0.35
            elif days_since_registration <= 60:
                return_probability = 0.25
            elif days_since_registration <= 90:
                return_probability = 0.18
            else:
                return_probability = 0.10

            if random.random() > return_probability:
                break

            days_to_next_session = random.randint(3, 21)

            next_session = current_session + timedelta(
                days=days_to_next_session,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            if next_session > END_DATE:
                break

            session_starts.append(next_session)
            current_session = next_session

            # Ограничиваем количество сессий одного пользователя
            if len(session_starts) >= 8:
                break

        # -----------------------------
        # Генерация событий сессий
        # -----------------------------

        for session_number, session_start in enumerate(session_starts, start=1):

            session_id = (
                f"session_{int(user['user_id'])}_{session_number}"
            )

            # -----------------------------
            # 1. VISIT
            # -----------------------------

            rows.append({
                "event_id": event_id,
                "user_id": int(user["user_id"]),
                "event_time": session_start,
                "event_name": "visit",
                "product_id": None,
                "session_id": session_id
            })

            event_id += 1

            # 15% сессий заканчиваются после визита
            if random.random() < 0.15:
                continue

            # -----------------------------
            # 2. VIEW PRODUCT
            # -----------------------------

            product_id = random.choice(product_ids)

            view_time = session_start + timedelta(
                seconds=random.randint(10, 180)
            )

            if view_time > END_DATE:
                continue

            rows.append({
                "event_id": event_id,
                "user_id": int(user["user_id"]),
                "event_time": view_time,
                "event_name": "view_product",
                "product_id": product_id,
                "session_id": session_id
            })

            event_id += 1

            # A/B тест:
	    # control — текущая конверсия
            # test — немного более высокая вероятность добавления в корзину

            if user["experiment_group"] == "control":
            	drop_probability = 0.40
            else:
            	drop_probability = 0.32

            if random.random() < drop_probability:
            	continue

            # -----------------------------
            # 3. ADD TO CART
            # -----------------------------

            cart_time = view_time + timedelta(
                seconds=random.randint(30, 300)
            )

            if cart_time > END_DATE:
                continue

            rows.append({
                "event_id": event_id,
                "user_id": int(user["user_id"]),
                "event_time": cart_time,
                "event_name": "add_to_cart",
                "product_id": product_id,
                "session_id": session_id
            })

            event_id += 1

            # 30% сессий не доходят до checkout
            if random.random() < 0.30:
                continue

            # -----------------------------
            # 4. CHECKOUT
            # -----------------------------

            checkout_time = cart_time + timedelta(
                seconds=random.randint(30, 300)
            )

            if checkout_time > END_DATE:
                continue

            rows.append({
                "event_id": event_id,
                "user_id": int(user["user_id"]),
                "event_time": checkout_time,
                "event_name": "checkout",
                "product_id": product_id,
                "session_id": session_id
            })

            event_id += 1

            # 20% сессий не завершаются покупкой
            if random.random() < 0.20:
                continue

            # -----------------------------
            # 5. PURCHASE
            # -----------------------------

            purchase_time = checkout_time + timedelta(
                seconds=random.randint(30, 600)
            )

            if purchase_time > END_DATE:
                continue

            rows.append({
                "event_id": event_id,
                "user_id": int(user["user_id"]),
                "event_time": purchase_time,
                "event_name": "purchase",
                "product_id": product_id,
                "session_id": session_id
            })

            event_id += 1

    return pd.DataFrame(rows)

# -----------------------------
# Запуск генерации пользователей и товаров
# -----------------------------

users = generate_users(N_USERS)
products = generate_products()
print("\nЭкспериментальные группы:")
print(users["experiment_group"].value_counts())

# -----------------------------
# Запуск генерации событий
# -----------------------------

events = generate_events(users, products)

print(f"\nСоздано событий: {len(events)}")
print(events.head())

print("\nТипы событий:")
print(events["event_name"].value_counts())

print("\nПроверка последовательности:")
print(
    events
    .sort_values(["user_id", "event_time"])
    [["user_id", "event_name", "event_time"]]
    .head(20)
)
# -----------------------------
# Генерация заказов
# -----------------------------

def generate_orders(
    events: pd.DataFrame,
    products: pd.DataFrame
) -> pd.DataFrame:

    purchases = events[
        events["event_name"] == "purchase"
    ].copy()

    # Подтягиваем цену товара
    purchases = purchases.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left"
    )

    rows = []

    for order_id, (_, purchase) in enumerate(
        purchases.iterrows(),
        start=1
    ):

        quantity = random.choices(
            [1, 2, 3],
            weights=[75, 20, 5],
            k=1
        )[0]

        revenue = round(
            float(purchase["price"]) * quantity,
            2
        )

        rows.append({
            "order_id": order_id,
            "user_id": int(purchase["user_id"]),
            "order_time": purchase["event_time"],
            "product_id": int(purchase["product_id"]),
            "quantity": quantity,
            "revenue": revenue
        })

    return pd.DataFrame(rows)


# -----------------------------
# Запуск генерации заказов
# -----------------------------

orders = generate_orders(events, products)

print(f"\nСоздано заказов: {len(orders)}")
print(orders.head())

print("\nОбщая выручка:")
print(round(orders["revenue"].sum(), 2))

print("\nСредний чек:")
print(round(orders["revenue"].mean(), 2))
# -----------------------------
# Сохранение данных в CSV
# -----------------------------

users.to_csv(
    "data/users.csv",
    index=False
)

products.to_csv(
    "data/products.csv",
    index=False
)

events.to_csv(
    "data/events.csv",
    index=False
)

orders.to_csv(
    "data/orders.csv",
    index=False
)

print("\nCSV-файлы успешно сохранены:")
print("data/users.csv")
print("data/products.csv")
print("data/events.csv")
print("data/orders.csv")