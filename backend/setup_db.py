
import psycopg
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
from config import ADMIN_USERNAME, ADMIN_PASSWORD

print("=== O_Shop: Настройка базы данных ===\n")

print(f"[1/4] Подключаюсь к PostgreSQL как {POSTGRES_USER}...")
try:
    conn = psycopg.connect(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname="postgres",
        autocommit=True,
    )
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_DB,))
    if cur.fetchone():
        print(f"       База '{POSTGRES_DB}' уже существует — ОК")
    else:
        cur.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
        print(f"       База '{POSTGRES_DB}' создана!")

    cur.close()
    conn.close()
except Exception as e:
    print(f"\n[ОШИБКА] Не могу подключиться к PostgreSQL: {e}")
    print("\nПроверь:")
    print("  1. PostgreSQL установлен и запущен")
    print("  2. Пользователь 'postgres' с паролем 'postgres'")
    print("     (пароль задаётся при установке PostgreSQL)")
    print(f"  3. Порт {POSTGRES_PORT} свободен")
    exit(1)

print("[2/4] Создаю таблицы через SQLAlchemy ORM...")
from database import engine, Base
from models import User, Product, CartItem

Base.metadata.create_all(bind=engine)
print("       Таблицы users, products, cart_items — ОК")

print(f"[3/4] Создаю админа (login: {ADMIN_USERNAME})...")
from database import SessionLocal
from security import hash_password

db = SessionLocal()
existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
if existing:
    print(f"       Админ '{ADMIN_USERNAME}' уже есть — ОК")
else:
    admin = User(
        username=ADMIN_USERNAME,
        email=f"{ADMIN_USERNAME}@oshop.local",
        password_hash=hash_password(ADMIN_PASSWORD),
        role="admin",
    )
    db.add(admin)
    db.commit()
    print(f"       Админ создан! login: {ADMIN_USERNAME} / password: {ADMIN_PASSWORD}")
db.close()

print("[4/4] Добавляю тестовые товары...")
db = SessionLocal()
if db.query(Product).count() == 0:
    products = [
        Product(name="Laptop", description="Мощный ноутбук для работы", price=999.99, stock=10),
        Product(name="Headphones", description="Беспроводные наушники", price=79.99, stock=25),
        Product(name="Mouse", description="Игровая мышка", price=49.99, stock=50),
        Product(name="Keyboard", description="Механическая клавиатура", price=129.99, stock=15),
        Product(name="Monitor", description="27 дюймов, 144Hz", price=349.99, stock=8),
    ]
    db.add_all(products)
    db.commit()
    print(f"       Добавлено {len(products)} товаров!")
else:
    print(f"       Товары уже есть ({db.query(Product).count()} шт.) — ОК")
db.close()

print("\n=== Готово! ===")
print(f"  БД: {POSTGRES_DB} на localhost:{POSTGRES_PORT}")
print(f"  Админ: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
print(f"\nТеперь запусти сервер: python run.py")
