
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_database():
    """Создаёт базу zonik, если её нет"""

    host = input("Host (по умолчанию localhost): ") or "localhost"
    port = input("Port (по умолчанию 5432): ") or "5432"
    user = input("User (по умолчанию postgres): ") or "postgres"
    password = input("Password: ")
    db_name = input("Имя базы (по умолчанию zonik): ") or "zonik"

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ База данных '{db_name}' создана")
        else:
            print(f"ℹ️ База данных '{db_name}' уже существует")

        cur.close()
        conn.close()

        print("\n📝 Теперь выполни SQL-скрипты из папки database/ по порядку:")
        print("   1. 01_schema.sql")
        print("   2. 02_seed_data.sql")
        print("   3. 03_functions_triggers.sql")
        print("   4. 04_views.sql")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    create_database()