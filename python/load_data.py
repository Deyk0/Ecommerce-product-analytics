import pandas as pd
import psycopg2


# -----------------------------
# Подключение к PostgreSQL
# -----------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ecommerce_analytics",
    user="postgres",
    password=input("Введите пароль PostgreSQL: ")
)

cur = conn.cursor()


# -----------------------------
# Загрузка CSV
# -----------------------------

print("Читаем CSV-файлы...")

users = pd.read_csv("data/users.csv")
products = pd.read_csv("data/products.csv")
events = pd.read_csv("data/events.csv")
orders = pd.read_csv("data/orders.csv")

print(f"Пользователей: {len(users)}")
print(f"Товаров: {len(products)}")
print(f"Событий: {len(events)}")
print(f"Заказов: {len(orders)}")


# -----------------------------
# Загрузка users
# -----------------------------

print("\nЗагружаем users...")

for row in users.itertuples(index=False, name=None):
    cur.execute(
        """
        INSERT INTO users (
            user_id,
            registration_date,
            country,
            device,
            traffic_source
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        row
    )


# -----------------------------
# Загрузка products
# -----------------------------

print("Загружаем products...")

for row in products.itertuples(index=False, name=None):
    cur.execute(
        """
        INSERT INTO products (
            product_id,
            category,
            price
        )
        VALUES (%s, %s, %s)
        """,
        row
    )


# -----------------------------
# Загрузка events
# -----------------------------

print("Загружаем events...")

for row in events.itertuples(index=False, name=None):
    product_id = None if pd.isna(row[4]) else int(row[4])

    cur.execute(
        """
        INSERT INTO events (
            event_id,
            user_id,
            event_time,
            event_name,
            product_id,
            session_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            int(row[0]),
            int(row[1]),
            row[2],
            row[3],
            product_id,
            row[5]
        )
    )


# -----------------------------
# Загрузка orders
# -----------------------------

print("Загружаем orders...")

for row in orders.itertuples(index=False, name=None):
    cur.execute(
        """
        INSERT INTO orders (
            order_id,
            user_id,
            order_time,
            product_id,
            quantity,
            revenue
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        row
    )


# -----------------------------
# Сохранение
# -----------------------------

conn.commit()

print("\nДанные успешно загружены в PostgreSQL.")

cur.close()
conn.close()