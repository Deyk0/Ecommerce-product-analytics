import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

DB_USER = "postgres"
DB_PASSWORD = input("Введите пароль PostgreSQL: ")
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ecommerce_analytics"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Загрузка данных
users = pd.read_sql("SELECT * FROM users", engine)
products = pd.read_sql("SELECT * FROM products", engine)
events = pd.read_sql("SELECT * FROM events", engine)
orders = pd.read_sql("SELECT * FROM orders", engine)

# Приведение дат
users["registration_date"] = pd.to_datetime(users["registration_date"])
events["event_time"] = pd.to_datetime(events["event_time"])
orders["order_time"] = pd.to_datetime(orders["order_time"])

# Проверка пропусков
print("=== Пропуски ===")
print("\nUsers:")
print(users.isna().sum())

print("\nProducts:")
print(products.isna().sum())

print("\nEvents:")
print(events.isna().sum())

print("\nOrders:")
print(orders.isna().sum())

# Проверка дубликатов
print("\n=== Дубликаты ===")
print(f"Users: {users.duplicated().sum()}")
print(f"Products: {products.duplicated().sum()}")
print(f"Events: {events.duplicated().sum()}")
print(f"Orders: {orders.duplicated().sum()}")

# Диапазон дат
print("\n=== Диапазон дат ===")
print(f"Events: {events['event_time'].min()} — {events['event_time'].max()}")
print(f"Orders: {orders['order_time'].min()} — {orders['order_time'].max()}")

# Проверка событий до регистрации
events_with_users = events.merge(
    users[["user_id", "registration_date"]],
    on="user_id",
    how="left"
)

events_before_registration = (
    events_with_users["event_time"].dt.date
    < events_with_users["registration_date"].dt.date
).sum()

print("\n=== Проверка логики данных ===")
print(
    f"Событий до регистрации пользователя: "
    f"{events_before_registration}"
)

# ============================================
# DAU — Daily Active Users
# ============================================

dau = (
    events
    .assign(activity_date=events["event_time"].dt.date)
    .groupby("activity_date")["user_id"]
    .nunique()
    .reset_index(name="dau")
)

print("\n=== DAU ===")
print(dau.head())
print(f"Средний DAU: {dau['dau'].mean():.0f}")
print(f"Максимальный DAU: {dau['dau'].max():.0f}")
print(f"Минимальный DAU: {dau['dau'].min():.0f}")

# ============================================
# WAU — Weekly Active Users
# ============================================

wau = (
    events
    .assign(week=events["event_time"].dt.to_period("W").dt.start_time)
    .groupby("week")["user_id"]
    .nunique()
    .reset_index(name="wau")
)

print("\n=== WAU ===")
print(wau.to_string(index=False))


# ============================================
# MAU — Monthly Active Users
# ============================================

mau = (
    events
    .assign(month=events["event_time"].dt.to_period("M").dt.start_time)
    .groupby("month")["user_id"]
    .nunique()
    .reset_index(name="mau")
)

print("\n=== MAU ===")
print(mau.to_string(index=False))

# ============================================
# DAU / MAU — Stickiness
# ============================================

dau["month"] = pd.to_datetime(dau["activity_date"]).dt.to_period("M").dt.start_time

avg_dau_by_month = (
    dau
    .groupby("month")["dau"]
    .mean()
    .reset_index(name="avg_dau")
)

stickiness = avg_dau_by_month.merge(
    mau,
    on="month",
    how="inner"
)

stickiness["dau_mau_percent"] = (
    stickiness["avg_dau"] / stickiness["mau"] * 100
)

print("\n=== DAU / MAU ===")
print(
    stickiness[
        ["month", "avg_dau", "mau", "dau_mau_percent"]
    ].to_string(index=False)
)

# ============================================
# DAU visualization
# ============================================

plt.figure(figsize=(12, 5))

plt.plot(
    dau["activity_date"],
    dau["dau"]
)

plt.title("Daily Active Users (DAU)")
plt.xlabel("Date")
plt.ylabel("Active users")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    "report/dau.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# MAU visualization
# ============================================

plt.figure(figsize=(10, 5))

plt.plot(
    mau["month"],
    mau["mau"],
    marker="o"
)

plt.title("Monthly Active Users (MAU)")
plt.xlabel("Month")
plt.ylabel("Active users")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    "report/mau.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# DAU / MAU visualization
# ============================================

plt.figure(figsize=(10, 5))

plt.plot(
    stickiness["month"],
    stickiness["dau_mau_percent"],
    marker="o"
)

plt.title("DAU / MAU")
plt.xlabel("Month")
plt.ylabel("DAU / MAU, %")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    "report/dau_mau.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# Funnel analysis
# ============================================

event_times = (
    events
    .pivot_table(
        index="user_id",
        columns="event_name",
        values="event_time",
        aggfunc="min"
    )
    .reset_index()
)

# Проверяем последовательность событий
event_times["view_time"] = event_times["view_product"].where(
    event_times["view_product"] > event_times["visit"]
)

event_times["cart_time"] = event_times["add_to_cart"].where(
    event_times["add_to_cart"] > event_times["view_time"]
)

event_times["checkout_time"] = event_times["checkout"].where(
    event_times["checkout"] > event_times["cart_time"]
)

event_times["purchase_time"] = event_times["purchase"].where(
    event_times["purchase"] > event_times["checkout_time"]
)


# ============================================
# Sequential funnel
# ============================================

funnel = pd.DataFrame({
    "stage": [
        "visit",
        "view_product",
        "add_to_cart",
        "checkout",
        "purchase"
    ],
    "users": [
        event_times["visit"].notna().sum(),
        event_times["view_time"].notna().sum(),
        event_times["cart_time"].notna().sum(),
        event_times["checkout_time"].notna().sum(),
        event_times["purchase_time"].notna().sum()
    ]
})

funnel["conversion_from_visit"] = (
    funnel["users"]
    / funnel.loc[0, "users"]
    * 100
)

print("\n=== FUNNEL ===")
print(funnel)


# ============================================
# Funnel visualization
# ============================================

plt.figure(figsize=(10, 6))

plt.bar(
    funnel["stage"],
    funnel["users"]
)

plt.title("E-commerce Conversion Funnel")
plt.xlabel("Funnel stage")
plt.ylabel("Unique users")
plt.xticks(rotation=20)

for i, value in enumerate(funnel["users"]):
    plt.text(
        i,
        value,
        f"{value:,}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "report/funnel.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()


# ============================================
# Funnel step conversion
# ============================================

funnel["step_conversion"] = (
    funnel["users"]
    / funnel["users"].shift(1)
    * 100
)

funnel.loc[0, "step_conversion"] = 100

print("\n=== FUNNEL STEP CONVERSION ===")
print(
    funnel[
        ["stage", "users", "step_conversion"]
    ]
)


# ============================================
# Funnel step conversion visualization
# ============================================

step_conversion = funnel.iloc[1:].copy()

step_conversion["transition"] = (
    funnel["stage"].shift(1).iloc[1:].values
    + " → "
    + funnel["stage"].iloc[1:].values
)

plt.figure(figsize=(10, 5))

plt.bar(
    step_conversion["transition"],
    step_conversion["step_conversion"]
)

plt.title("Conversion Between Funnel Steps")
plt.xlabel("Transition")
plt.ylabel("Conversion, %")
plt.ylim(0, 100)
plt.xticks(rotation=20)

for i, value in enumerate(step_conversion["step_conversion"]):
    plt.text(
        i,
        value,
        f"{value:.1f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "report/funnel_step_conversion.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# Revenue metrics
# ============================================

total_revenue = orders["revenue"].sum()
total_orders = orders["order_id"].nunique()
aov = total_revenue / total_orders

print("\n=== REVENUE METRICS ===")
print(f"Total revenue: {total_revenue:,.2f}")
print(f"Total orders: {total_orders:,}")
print(f"AOV: {aov:,.2f}")

# ============================================
# Monthly revenue
# ============================================

monthly_revenue = (
    orders
    .assign(month=orders["order_time"].dt.to_period("M").dt.start_time)
    .groupby("month")
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique")
    )
    .reset_index()
)

monthly_revenue["aov"] = (
    monthly_revenue["revenue"]
    / monthly_revenue["orders"]
)

print("\n=== MONTHLY REVENUE ===")
print(monthly_revenue)

# ============================================
# Monthly revenue visualization
# ============================================

plt.figure(figsize=(10, 5))

plt.plot(
    monthly_revenue["month"],
    monthly_revenue["revenue"],
    marker="o"
)

plt.title("Monthly Revenue")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    "report/monthly_revenue.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# Revenue by product category
# ============================================

revenue_by_category = (
    orders
    .merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left"
    )
    .groupby("category")
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique")
    )
    .reset_index()
    .sort_values("revenue", ascending=False)
)

revenue_by_category["revenue_share"] = (
    revenue_by_category["revenue"]
    / revenue_by_category["revenue"].sum()
    * 100
)

print("\n=== REVENUE BY CATEGORY ===")
print(revenue_by_category)

# ============================================
# Revenue by category visualization
# ============================================

plt.figure(figsize=(10, 6))

plt.bar(
    revenue_by_category["category"],
    revenue_by_category["revenue"]
)

plt.title("Revenue by Product Category")
plt.xlabel("Category")
plt.ylabel("Revenue")
plt.xticks(rotation=30)

plt.tight_layout()

plt.savefig(
    "report/revenue_by_category.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

# ============================================
# ARPPU
# ============================================

paying_users = orders["user_id"].nunique()
arppu = total_revenue / paying_users

print("\n=== ARPPU ===")
print(f"Paying users: {paying_users:,}")
print(f"ARPPU: {arppu:,.2f}")

# ============================================
# Purchases per user
# ============================================

purchases_per_user = (
    orders
    .groupby("user_id")["order_id"]
    .nunique()
    .value_counts()
    .sort_index()
    .reset_index()
)

purchases_per_user.columns = ["purchase_count", "users"]

repeat_buyers = (
    purchases_per_user
    .loc[purchases_per_user["purchase_count"] >= 2, "users"]
    .sum()
)

repeat_buyer_share = (
    repeat_buyers / paying_users * 100
)

print("\n=== PURCHASES PER USER ===")
print(purchases_per_user)

print(f"\nRepeat buyers: {repeat_buyers:,}")
print(f"Repeat buyer share: {repeat_buyer_share:.2f}%")

# ============================================
# Purchases per user visualization
# ============================================

plt.figure(figsize=(9, 5))

plt.bar(
    purchases_per_user["purchase_count"].astype(str),
    purchases_per_user["users"]
)

plt.title("Purchases per User")
plt.xlabel("Number of purchases")
plt.ylabel("Users")

for i, value in enumerate(purchases_per_user["users"]):
    plt.text(
        i,
        value,
        f"{value:,}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "report/purchases_per_user.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()
# ============================================
# Cohort Retention — 30-day periods
# ============================================

events_with_registration = events.merge(
    users[["user_id", "registration_date"]],
    on="user_id",
    how="left"
)

# Приводим дату события к дате без времени,
# чтобы методология совпадала с SQL
events_with_registration["event_date"] = (
    events_with_registration["event_time"].dt.normalize()
)

events_with_registration["registration_date"] = pd.to_datetime(
    events_with_registration["registration_date"]
)

# Количество дней с момента регистрации
events_with_registration["days_since_registration"] = (
    events_with_registration["event_date"]
    - events_with_registration["registration_date"]
).dt.days

# Оставляем только события после регистрации
events_with_registration = events_with_registration[
    events_with_registration["days_since_registration"] >= 0
].copy()

# 30-дневные периоды:
# M+0 = 0–29 дней
# M+1 = 30–59 дней
# M+2 = 60–89 дней
events_with_registration["retention_month"] = (
    events_with_registration["days_since_registration"] // 30
).astype(int)

# Когорта = месяц регистрации
events_with_registration["cohort_month"] = (
    events_with_registration["registration_date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

# Размер каждой когорты
cohort_sizes = (
    users.assign(
        cohort_month=(
            pd.to_datetime(users["registration_date"])
            .dt.to_period("M")
            .dt.to_timestamp()
        )
    )
    .groupby("cohort_month")
    .agg(
        cohort_size=("user_id", "nunique"),
        cohort_last_registration=("registration_date", "max")
    )
    .reset_index()
)

cohort_activity = (
    events_with_registration
    .groupby(
        ["cohort_month", "retention_month"]
    )["user_id"]
    .nunique()
    .reset_index(name="active_users")
)

# Создаем полный набор когорт × retention periods
periods = range(
    int(events_with_registration["retention_month"].max()) + 1
)

cohort_period_grid = (
    cohort_sizes[["cohort_month"]]
    .assign(key=1)
    .merge(
        pd.DataFrame({
            "retention_month": list(periods),
            "key": 1
        }),
        on="key"
    )
    .drop(columns="key")
)

cohort_retention = cohort_period_grid.merge(
    cohort_sizes,
    on="cohort_month",
    how="left"
)

cohort_retention = cohort_retention.merge(
    cohort_activity,
    on=["cohort_month", "retention_month"],
    how="left"
)

# Если период полностью наблюдаем, отсутствие активности = 0
cohort_retention["active_users"] = (
    cohort_retention["active_users"]
    .fillna(0)
    .astype(float)
)

# Последняя дата, до которой у нас есть данные
data_end_date = events_with_registration["event_date"].max()

# Конец retention-периода
cohort_retention["period_end"] = (
    pd.to_datetime(
        cohort_retention["cohort_last_registration"]
    )
    + pd.to_timedelta(
        (cohort_retention["retention_month"] + 1) * 30 - 1,
        unit="D"
    )
)

# Если весь retention-период еще не наблюдаем,
# значение retention не рассчитываем
cohort_retention.loc[
    cohort_retention["period_end"] > data_end_date,
    "active_users"
] = float("nan")

cohort_retention["retention"] = (
    cohort_retention["active_users"]
    / cohort_retention["cohort_size"]
    * 100
)

retention_matrix = (
    cohort_retention
    .pivot(
        index="cohort_month",
        columns="retention_month",
        values="retention"
    )
)

retention_matrix.columns = [
    f"M+{int(column)}"
    for column in retention_matrix.columns
]

print("\nCohort retention:")
print(retention_matrix.round(2))

print("\n===== COHORT RETENTION MATRIX =====")
print(retention_matrix.round(2))

# ============================================
# Cohort Retention Heatmap
# ============================================

plt.figure(figsize=(10, 6))

plt.imshow(
    retention_matrix,
    aspect="auto",
    interpolation="nearest"
)

plt.colorbar(label="Retention, %")

plt.xticks(
    range(len(retention_matrix.columns)),
    retention_matrix.columns
)

plt.yticks(
    range(len(retention_matrix.index)),
    retention_matrix.index.strftime("%Y-%m")
)

plt.xlabel("Retention period")
plt.ylabel("Cohort")
plt.title("Cohort Retention — 30-day periods")

# Показываем значения внутри ячеек
for i in range(len(retention_matrix.index)):
    for j in range(len(retention_matrix.columns)):
        value = retention_matrix.iloc[i, j]

        if pd.notna(value):
            plt.text(
                j,
                i,
                f"{value:.1f}%",
                ha="center",
                va="center"
            )

plt.tight_layout()

plt.savefig(
    "report/cohort_retention.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()
# ============================================
# Time to Second Purchase
# ============================================

purchase_dates = (
    orders
    .sort_values(["user_id", "order_time"])
    .groupby("user_id")["order_time"]
    .apply(list)
)

time_to_second_purchase = []

for user_id, dates in purchase_dates.items():
    if len(dates) >= 2:
        days = (dates[1] - dates[0]).total_seconds() / 86400
        time_to_second_purchase.append(days)

time_to_second_purchase = pd.Series(
    time_to_second_purchase,
    name="days_to_second_purchase"
)

print("\nTime to second purchase:")
print(f"Repeat buyers: {len(time_to_second_purchase):,}")
print(
    f"Average days: "
    f"{time_to_second_purchase.mean():.2f}"
)
print(
    f"Median days: "
    f"{time_to_second_purchase.median():.2f}"
)
# ============================================
# Time to Second Purchase Distribution
# ============================================

bins = [0, 7, 14, 30, 60, float("inf")]
labels = ["0-7 days", "8-14 days", "15-30 days", "31-60 days", "60+ days"]

time_to_second_purchase_buckets = pd.cut(
    time_to_second_purchase,
    bins=bins,
    labels=labels,
    include_lowest=True
)

time_to_second_purchase_distribution = (
    time_to_second_purchase_buckets
    .value_counts()
    .reindex(labels)
    .reset_index()
)

time_to_second_purchase_distribution.columns = [
    "period",
    "users"
]

time_to_second_purchase_distribution["share"] = (
    time_to_second_purchase_distribution["users"]
    / time_to_second_purchase_distribution["users"].sum()
    * 100
)

print("\nTime to second purchase distribution:")
print(time_to_second_purchase_distribution)
# ============================================
# Time to Second Purchase Visualization
# ============================================

plt.figure(figsize=(9, 5))

plt.bar(
    time_to_second_purchase_distribution["period"],
    time_to_second_purchase_distribution["share"]
)

plt.title("Time to Second Purchase")
plt.xlabel("Time period")
plt.ylabel("Share of repeat buyers, %")

for i, value in enumerate(
    time_to_second_purchase_distribution["share"]
):
    plt.text(
        i,
        value,
        f"{value:.1f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "report/time_to_second_purchase.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()
# ============================================
# Conversion by Device
# ============================================

events_with_device = events.merge(
    users[["user_id", "device"]],
    on="user_id",
    how="left"
)

device_conversion = (
    events_with_device
    .groupby("device")["session_id"]
    .nunique()
    .reset_index(name="sessions")
)

device_purchases = (
    events_with_device[
        events_with_device["event_name"] == "purchase"
    ]
    .groupby("device")["session_id"]
    .nunique()
    .reset_index(name="purchase_sessions")
)

device_conversion = device_conversion.merge(
    device_purchases,
    on="device",
    how="left"
)

device_conversion["conversion"] = (
    device_conversion["purchase_sessions"]
    / device_conversion["sessions"]
    * 100
)
# =========================
# A/B TEST
# =========================

ab_events = events[
    events["event_name"].isin([
        "view_product",
        "add_to_cart"
    ])
].copy()

ab_events = ab_events.merge(
    users[["user_id", "experiment_group"]],
    on="user_id",
    how="left"
)

ab_sessions = (
    ab_events
    .groupby(
        ["experiment_group", "user_id", "session_id", "event_name"],
        as_index=False
    )["event_time"]
    .min()
)

ab_sessions = (
    ab_sessions
    .pivot_table(
        index=["experiment_group", "user_id", "session_id"],
        columns="event_name",
        values="event_time",
        aggfunc="min"
    )
    .reset_index()
)

ab_sessions["converted"] = (
    ab_sessions["view_product"].notna()
    & ab_sessions["add_to_cart"].notna()
    & (
        ab_sessions["add_to_cart"]
        > ab_sessions["view_product"]
    )
)

ab_results = (
    ab_sessions[
        ab_sessions["view_product"].notna()
    ]
    .groupby("experiment_group")
    .agg(
        sessions_viewed=("session_id", "count"),
        sessions_added=("converted", "sum")
    )
    .reset_index()
)

ab_results["conversion_percent"] = (
    ab_results["sessions_added"]
    / ab_results["sessions_viewed"]
    * 100
)

print("\n=== A/B TEST ===")
print(ab_results)
plt.figure(figsize=(8, 5))

plt.bar(
    ab_results["experiment_group"],
    ab_results["conversion_percent"]
)

plt.title("A/B Test: View Product → Add to Cart")
plt.xlabel("Experiment group")
plt.ylabel("Conversion (%)")
plt.ylim(0, 100)

for i, value in enumerate(ab_results["conversion_percent"]):
    plt.text(
        i,
        value + 2,
        f"{value:.2f}%",
        ha="center"
    )

plt.tight_layout()
plt.savefig(
    "report/ab_test_conversion.png",
    dpi=150
)
plt.close()
print("\nConversion by device:")
print(device_conversion)
# ============================================
# Conversion by Traffic Source
# ============================================

source_conversion = (
    events
    .merge(
        users[["user_id", "traffic_source"]],
        on="user_id",
        how="left"
    )
    .groupby("traffic_source")["session_id"]
    .nunique()
    .reset_index(name="sessions")
)

source_purchases = (
    events
    .merge(
        users[["user_id", "traffic_source"]],
        on="user_id",
        how="left"
    )
)

source_purchases = (
    source_purchases[
        source_purchases["event_name"] == "purchase"
    ]
    .groupby("traffic_source")["session_id"]
    .nunique()
    .reset_index(name="purchase_sessions")
)

source_conversion = source_conversion.merge(
    source_purchases,
    on="traffic_source",
    how="left"
)

source_conversion["conversion"] = (
    source_conversion["purchase_sessions"]
    / source_conversion["sessions"]
    * 100
)

source_conversion = source_conversion.sort_values(
    "conversion",
    ascending=False
)

print("\nConversion by traffic source:")
# ============================================
# Traffic Source Conversion Visualization
# ============================================

plt.figure(figsize=(10, 5))

plt.bar(
    source_conversion["traffic_source"],
    source_conversion["conversion"]
)

plt.title("Conversion by Traffic Source")
plt.xlabel("Traffic Source")
plt.ylabel("Conversion, %")

for i, value in enumerate(source_conversion["conversion"]):
    plt.text(
        i,
        value,
        f"{value:.2f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "report/conversion_by_traffic_source.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()
print(source_conversion)