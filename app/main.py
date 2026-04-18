# app/main.py

import psycopg2
from tabulate import tabulate
from colorama import init, Fore, Style
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.db_config import DB_CONFIG
except ImportError:
    from db_config import DB_CONFIG
init(autoreset=True)

# Глобальные переменные сессии
current_user = None  # {'role': 'customer', 'id': 1, 'name': 'Иван'}
current_seller = None  # {'id': 1, 'store_name': 'Магазин'}


def get_connection():
    """Подключение с настройками из DB_CONFIG"""
    try:
        if not DB_CONFIG['password']:
            DB_CONFIG['password'] = input(Fore.YELLOW + "Введи пароль от postgres: ")

        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(Fore.RED + f"❌ Ошибка подключения: {e}")
        print(Fore.YELLOW + "Проверь настройки в app/db_config.py")
        return None


# ============================================
# АВТОРИЗАЦИЯ
# ============================================

def login_menu():
    """Меню входа в систему"""
    global current_user, current_seller

    while True:
        print(Fore.MAGENTA + Style.BRIGHT + "\n" + "=" * 50)
        print(Fore.MAGENTA + Style.BRIGHT + "        🔐 ВХОД В ZONIK")
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 50)
        print(Fore.WHITE + "1. 👤 Войти как покупатель")
        print(Fore.WHITE + "2. 🏪 Войти как продавец")
        print(Fore.WHITE + "3. 🆕 Регистрация покупателя")
        print(Fore.WHITE + "4. 🚪 Выход")
        print(Fore.MAGENTA + "-" * 50)

        choice = input(Fore.YELLOW + "Выбери (1-4): ")

        if choice == '1':
            customer_login()
            if current_user:
                return 'customer'
        elif choice == '2':
            seller_login()
            if current_seller:
                return 'seller'
        elif choice == '3':
            register_customer()
        elif choice == '4':
            print(Fore.CYAN + "\n👋 До встречи в Zonik!")
            return None
        else:
            print(Fore.RED + "❌ Неверный выбор")


def customer_login():
    """Вход как покупатель"""
    global current_user

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    print(Fore.MAGENTA + "\n👤 ВХОД ПОКУПАТЕЛЯ")
    phone = input(Fore.YELLOW + "Номер телефона (11 цифр): ")

    cur.execute("SELECT Customer_ID, Full_Name FROM Customers WHERE Phone = %s", (phone,))
    result = cur.fetchone()

    if result:
        current_user = {
            'role': 'customer',
            'id': result[0],
            'name': result[1]
        }
        print(Fore.GREEN + f"\n✅ Добро пожаловать, {result[1]}!")
    else:
        print(Fore.RED + "❌ Покупатель не найден. Зарегистрируйтесь.")
        current_user = None

    cur.close()
    conn.close()


def register_customer():
    """Регистрация нового покупателя"""
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    print(Fore.MAGENTA + "\n🆕 РЕГИСТРАЦИЯ ПОКУПАТЕЛЯ")
    phone = input(Fore.YELLOW + "Номер телефона (11 цифр): ")

    cur.execute("SELECT Customer_ID FROM Customers WHERE Phone = %s", (phone,))
    if cur.fetchone():
        print(Fore.RED + "❌ Этот номер уже зарегистрирован. Войдите.")
        cur.close()
        conn.close()
        return

    name = input(Fore.YELLOW + "ФИО: ")
    email = input(Fore.YELLOW + "Email (Enter чтобы пропустить): ") or None
    address = input(Fore.YELLOW + "Адрес доставки: ")

    cur.execute("""
        INSERT INTO Customers (Full_Name, Phone, Email, Address)
        VALUES (%s, %s, %s, %s)
    """, (name, phone, email, address))

    conn.commit()

    print(Fore.GREEN + f"✅ Регистрация успешна! Теперь войдите.")

    cur.close()
    conn.close()


def seller_login():
    """Вход как продавец"""
    global current_seller

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    print(Fore.MAGENTA + "\n🏪 ВХОД ПРОДАВЦА")
    seller_id = input(Fore.YELLOW + "ID продавца: ")

    try:
        seller_id = int(seller_id)
    except ValueError:
        print(Fore.RED + "❌ ID должен быть числом")
        cur.close()
        conn.close()
        return

    cur.execute("SELECT Sellers_ID, Store_Name FROM Sellers WHERE Sellers_ID = %s", (seller_id,))
    result = cur.fetchone()

    if result:
        current_seller = {
            'id': result[0],
            'store_name': result[1]
        }
        print(Fore.GREEN + f"\n✅ Добро пожаловать, {result[1]}!")
    else:
        print(Fore.RED + "❌ Продавец не найден")
        current_seller = None

    cur.close()
    conn.close()


def logout():
    """Выход из аккаунта"""
    global current_user, current_seller
    current_user = None
    current_seller = None
    print(Fore.CYAN + "\n👋 Вы вышли из системы")


# ============================================
# МЕНЮ ПОКУПАТЕЛЯ
# ============================================

def show_catalog():
    """Показать все товары"""
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.Product_ID,
            p.Product_Name,
            s.Store_Name,
            p.Price,
            p.Stock_Quantity,
            c.Category_Name
        FROM Product p
        JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
        JOIN Category c ON p.Categories_ID = c.Categories_ID
        WHERE p.Stock_Quantity > 0
        ORDER BY p.Price
    """)

    rows = cur.fetchall()
    headers = ['ID', 'Товар', 'Продавец', 'Цена', 'В наличии', 'Категория']

    print(Fore.CYAN + Style.BRIGHT + "\n📦 КАТАЛОГ ТОВАРОВ")
    print(tabulate(rows, headers=headers, tablefmt='fancy_grid'))

    cur.close()
    conn.close()


def show_sellers():
    """Показать всех продавцов с рейтингом"""
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute("""
        SELECT Sellers_ID, Store_Name, Rating
        FROM Sellers
        ORDER BY Rating DESC
    """)

    rows = cur.fetchall()
    headers = ['ID', 'Магазин', 'Рейтинг']

    print(Fore.CYAN + Style.BRIGHT + "\n🏪 ПРОДАВЦЫ")
    print(tabulate(rows, headers=headers, tablefmt='fancy_grid'))

    cur.close()
    conn.close()


def show_catalog_short():
    """Показывает краткий каталог для выбора товара"""
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.Product_ID,
            p.Product_Name,
            p.Price,
            p.Stock_Quantity,
            s.Store_Name
        FROM Product p
        JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
        WHERE p.Stock_Quantity > 0
        ORDER BY p.Product_ID
    """)

    rows = cur.fetchall()
    headers = ['ID', 'Товар', 'Цена', 'В наличии', 'Продавец']

    print(Fore.CYAN + "\n📦 ДОСТУПНЫЕ ТОВАРЫ:")
    print(tabulate(rows, headers=headers, tablefmt='grid'))

    cur.close()
    conn.close()


def create_order():
    """Создание заказа с корзиной"""
    global current_user

    if not current_user:
        print(Fore.RED + "❌ Сначала войдите как покупатель!")
        return

    cart = []

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    while True:
        print(Fore.MAGENTA + "\n" + "=" * 50)
        print(Fore.MAGENTA + f"🛒 КОРЗИНА ({current_user['name']})")
        print(Fore.MAGENTA + "=" * 50)

        if cart:
            cart_total = sum(item['price'] * item['quantity'] for item in cart)
            print(Fore.CYAN + "\n📋 Текущая корзина:")

            cart_rows = []
            for i, item in enumerate(cart, 1):
                cart_rows.append([
                    i,
                    item['name'],
                    f"{item['price']} ₽",
                    item['quantity'],
                    f"{item['price'] * item['quantity']} ₽"
                ])

            print(tabulate(cart_rows, headers=['№', 'Товар', 'Цена', 'Кол-во', 'Сумма'], tablefmt='grid'))
            print(Fore.YELLOW + f"\n💰 Итого: {cart_total} ₽")
        else:
            print(Fore.YELLOW + "\n🛒 Корзина пуста")

        print(Fore.WHITE + "\n1. ➕ Добавить товар")
        print(Fore.WHITE + "2. ✅ Оформить заказ")
        print(Fore.WHITE + "3. ❌ Отмена")

        choice = input(Fore.YELLOW + "\nВыбери действие: ")

        if choice == '1':
            show_catalog_short()

            try:
                product_id = int(input(Fore.YELLOW + "\nID товара для добавления: "))
            except ValueError:
                print(Fore.RED + "❌ Введи число!")
                continue

            cur.execute("""
                SELECT Product_Name, Stock_Quantity, Price, Sellers_ID
                FROM Product 
                WHERE Product_ID = %s
            """, (product_id,))

            result = cur.fetchone()

            if not result:
                print(Fore.RED + "❌ Товар не найден")
                continue

            name, stock, price, seller_id = result

            if stock <= 0:
                print(Fore.RED + f"❌ Товара нет в наличии")
                continue

            print(Fore.CYAN + f"\n📦 {name} | Цена: {price} ₽ | В наличии: {stock} шт.")

            try:
                qty = int(input(Fore.YELLOW + "Количество: "))
            except ValueError:
                print(Fore.RED + "❌ Введи число!")
                continue

            if qty <= 0:
                print(Fore.RED + "❌ Количество должно быть больше нуля")
                continue

            if qty > stock:
                print(Fore.RED + f"❌ Недостаточно. В наличии: {stock}")
                continue

            found = False
            for item in cart:
                if item['product_id'] == product_id:
                    new_qty = item['quantity'] + qty
                    if new_qty > stock:
                        print(Fore.RED + f"❌ Всего в корзине будет {new_qty}, а в наличии {stock}")
                        continue
                    item['quantity'] = new_qty
                    found = True
                    print(Fore.GREEN + f"✅ Количество увеличено до {new_qty}")
                    break

            if not found:
                cart.append({
                    'product_id': product_id,
                    'name': name,
                    'price': price,
                    'quantity': qty,
                    'seller_id': seller_id
                })
                print(Fore.GREEN + f"✅ {name} добавлен в корзину")

        elif choice == '2':
            if not cart:
                print(Fore.RED + "❌ Корзина пуста! Добавь товары.")
                continue
            break

        elif choice == '3':
            print(Fore.YELLOW + "🚫 Заказ отменён")
            cur.close()
            conn.close()
            return
        else:
            print(Fore.RED + "❌ Неверный выбор")

    print(Fore.MAGENTA + "\n" + "=" * 50)
    print(Fore.MAGENTA + "💳 СПОСОБ ОПЛАТЫ")
    print(Fore.MAGENTA + "=" * 50)
    print("1. 💵 При получении")
    print("2. 💳 Картой онлайн")
    print("3. 📱 СБП")

    pay_choice = input(Fore.YELLOW + "Выбери способ оплаты (1-3): ")

    payment_methods = {
        '1': 'При получении',
        '2': 'Картой онлайн',
        '3': 'СБП'
    }

    payment_method = payment_methods.get(pay_choice, 'При получении')

    print(Fore.MAGENTA + "\n📦 АДРЕС ДОСТАВКИ")

    cur.execute("SELECT Address FROM Customers WHERE Customer_ID = %s", (current_user['id'],))
    saved_address = cur.fetchone()
    saved_address = saved_address[0] if saved_address else None

    if saved_address:
        print(Fore.CYAN + f"Сохранённый адрес: {saved_address}")
        use_saved = input(Fore.YELLOW + "Использовать этот адрес? (да/нет): ").lower()
        if use_saved in ['да', 'yes', 'y', '']:
            delivery_address = saved_address
        else:
            delivery_address = input(Fore.YELLOW + "Новый адрес доставки: ")
    else:
        delivery_address = input(Fore.YELLOW + "Адрес доставки: ")

    try:
        cart_total = sum(item['price'] * item['quantity'] for item in cart)

        cur.execute("""
                    INSERT INTO Orders (Customer_ID, Status, Total_Amount)
                    VALUES (%s, 'Ожидает', 0)
                    RETURNING Order_ID
                """, (current_user['id'],))

        order_id = cur.fetchone()[0]

        for item in cart:
            cur.execute("""
                INSERT INTO Orders_Item (Order_ID, Product_ID, Quantity, Price_At_Time)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))

        cur.execute("""
            INSERT INTO Payments (Order_ID, Payment_Method, Payment_Status, Date)
            VALUES (%s, %s, 'Ожидает', CURRENT_DATE)
        """, (order_id, payment_method))

        cur.execute("""
            INSERT INTO Delivery (Order_ID, Delivery_Address, Date, Delivery_Status)
            VALUES (%s, %s, CURRENT_DATE, 'Ожидает')
        """, (order_id, delivery_address))

        conn.commit()

        cur.execute("SELECT Total_Amount FROM Orders WHERE Order_ID = %s", (order_id,))
        cart_total = cur.fetchone()[0]
        
        print(Fore.GREEN + Style.BRIGHT + "\n" + "=" * 50)
        print(Fore.GREEN + Style.BRIGHT + f"✅ ЗАКАЗ №{order_id} УСПЕШНО ОФОРМЛЕН!")
        print(Fore.GREEN + "=" * 50)
        print(Fore.CYAN + f"👤 Покупатель: {current_user['name']}")
        print(Fore.CYAN + f"💰 Сумма: {cart_total} ₽")
        print(Fore.CYAN + f"💳 Оплата: {payment_method}")
        print(Fore.CYAN + f"📦 Доставка: {delivery_address}")
        print(Fore.CYAN + "\n📋 Состав заказа:")

        for item in cart:
            print(Fore.WHITE + f"   • {item['name']} x {item['quantity']} = {item['price'] * item['quantity']} ₽")

    except Exception as e:
        conn.rollback()
        print(Fore.RED + f"❌ Ошибка при оформлении: {e}")
    finally:
        cur.close()
        conn.close()


def show_my_orders():
    """Просмотр заказов текущего покупателя"""
    global current_user

    if not current_user:
        print(Fore.RED + "❌ Сначала войдите как покупатель!")
        return

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute("""
        SELECT 
            o.Order_ID,
            o.Order_Date,
            o.Status,
            o.Total_Amount,
            p.Payment_Method,
            p.Payment_Status,
            d.Delivery_Status
        FROM Orders o
        LEFT JOIN Payments p ON o.Order_ID = p.Order_ID
        LEFT JOIN Delivery d ON o.Order_ID = d.Order_ID
        WHERE o.Customer_ID = %s
        ORDER BY o.Order_Date DESC
    """, (current_user['id'],))

    orders = cur.fetchall()

    if not orders:
        print(Fore.YELLOW + f"\n📭 У вас пока нет заказов")
        cur.close()
        conn.close()
        return

    print(Fore.CYAN + Style.BRIGHT + f"\n📋 ЗАКАЗЫ {current_user['name']}")
    print(Fore.CYAN + "=" * 80)

    for order in orders:
        order_id, order_date, status, total, pay_method, pay_status, del_status = order

        print(Fore.YELLOW + Style.BRIGHT + f"\n🛍️ Заказ №{order_id} от {order_date}")
        print(Fore.WHITE + f"   Статус: {status} | Сумма: {total} ₽")
        print(Fore.WHITE + f"   Оплата: {pay_method} ({pay_status})")
        if del_status:
            print(Fore.WHITE + f"   Доставка: {del_status}")

        cur.execute("""
            SELECT 
                p.Product_Name,
                oi.Quantity,
                oi.Price_At_Time,
                s.Store_Name
            FROM Orders_Item oi
            JOIN Product p ON oi.Product_ID = p.Product_ID
            JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
            WHERE oi.Order_ID = %s
        """, (order_id,))

        items = cur.fetchall()

        print(Fore.CYAN + "   📦 Состав:")
        for item in items:
            product_name, qty, price, store = item
            print(Fore.WHITE + f"      • {product_name} x {qty} = {price * qty} ₽ (продавец: {store})")

    print(Fore.CYAN + "\n" + "=" * 80)

    cur.close()
    conn.close()


def show_analytics():
    """Аналитика: топ товаров по продажам"""
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.Product_Name,
            s.Store_Name,
            COALESCE(SUM(oi.Quantity), 0) AS Sold,
            COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0) AS Revenue
        FROM Product p
        JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
        LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
        GROUP BY p.Product_ID, p.Product_Name, s.Store_Name
        ORDER BY Revenue DESC
        LIMIT 10
    """)

    rows = cur.fetchall()
    headers = ['Товар', 'Продавец', 'Продано (шт)', 'Выручка (₽)']

    print(Fore.CYAN + Style.BRIGHT + "\n📊 ТОП-10 ТОВАРОВ ПО ВЫРУЧКЕ")
    print(tabulate(rows, headers=headers, tablefmt='fancy_grid'))

    cur.close()
    conn.close()


def customer_menu():
    """Меню покупателя"""
    while True:
        print(Fore.MAGENTA + Style.BRIGHT + "\n" + "=" * 50)
        print(Fore.MAGENTA + Style.BRIGHT + f"  🛒 ZONIK | {current_user['name']}")
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 50)
        print(Fore.WHITE + "1. 📦 Каталог товаров")
        print(Fore.WHITE + "2. 🏪 Продавцы")
        print(Fore.WHITE + "3. 🛍️  Создать заказ")
        print(Fore.WHITE + "4. 📋 Мои заказы")
        print(Fore.WHITE + "5. 🚪 Выйти из аккаунта")
        print(Fore.WHITE + "6. ❌ Выход из программы")
        print(Fore.MAGENTA + "-" * 50)

        choice = input(Fore.YELLOW + "Выбери (1-6): ")

        if choice == '1':
            show_catalog()
        elif choice == '2':
            show_sellers()
        elif choice == '3':
            create_order()
        elif choice == '4':
            show_my_orders()
        elif choice == '5':
            logout()
            return
        elif choice == '6':
            print(Fore.CYAN + "\n👋 До встречи в Zonik!")
            exit()
        else:
            print(Fore.RED + "❌ Неверный выбор")


# ============================================
# МЕНЮ ПРОДАВЦА
# ============================================

def add_product():
    """Добавление нового товара продавцом"""
    global current_seller

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    print(Fore.MAGENTA + "\n➕ ДОБАВЛЕНИЕ ТОВАРА")

    name = input(Fore.YELLOW + "Название товара: ")
    description = input(Fore.YELLOW + "Описание (Enter чтобы пропустить): ") or None

    try:
        price = float(input(Fore.YELLOW + "Цена: "))
        stock = int(input(Fore.YELLOW + "Количество на складе: "))
    except ValueError:
        print(Fore.RED + "❌ Цена и количество должны быть числами")
        cur.close()
        conn.close()
        return

    # Показываем категории
    cur.execute("SELECT Categories_ID, Category_Name FROM Category ORDER BY Categories_ID")
    categories = cur.fetchall()

    print(Fore.CYAN + "\n📂 ДОСТУПНЫЕ КАТЕГОРИИ:")
    for cat_id, cat_name in categories:
        print(Fore.WHITE + f"   {cat_id}. {cat_name}")

    try:
        cat_id = int(input(Fore.YELLOW + "ID категории: "))
    except ValueError:
        print(Fore.RED + "❌ ID категории должен быть числом")
        cur.close()
        conn.close()
        return

    cur.execute("""
        INSERT INTO Product (Product_Name, Product_Description, Price, Categories_ID, Stock_Quantity, Sellers_ID)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING Product_ID
    """, (name, description, price, cat_id, stock, current_seller['id']))

    product_id = cur.fetchone()[0]
    conn.commit()

    print(Fore.GREEN + f"\n✅ Товар '{name}' добавлен! ID: {product_id}")

    cur.close()
    conn.close()


def show_my_products():
    """Просмотр товаров продавца"""
    global current_seller

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.Product_ID,
            p.Product_Name,
            p.Price,
            p.Stock_Quantity,
            c.Category_Name,
            COALESCE(SUM(oi.Quantity), 0) AS Sold
        FROM Product p
        JOIN Category c ON p.Categories_ID = c.Categories_ID
        LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
        WHERE p.Sellers_ID = %s
        GROUP BY p.Product_ID, p.Product_Name, p.Price, p.Stock_Quantity, c.Category_Name
        ORDER BY p.Product_ID
    """, (current_seller['id'],))

    rows = cur.fetchall()

    if not rows:
        print(Fore.YELLOW + "\n📭 У вас пока нет товаров")
    else:
        headers = ['ID', 'Товар', 'Цена', 'В наличии', 'Категория', 'Продано']
        print(Fore.CYAN + Style.BRIGHT + f"\n📦 МОИ ТОВАРЫ ({current_seller['store_name']})")
        print(tabulate(rows, headers=headers, tablefmt='fancy_grid'))

    cur.close()
    conn.close()


def update_stock():
    """Обновление остатков товара"""
    global current_seller

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    show_my_products()

    try:
        product_id = int(input(Fore.YELLOW + "\nID товара для обновления: "))
        new_stock = int(input(Fore.YELLOW + "Новое количество: "))
    except ValueError:
        print(Fore.RED + "❌ Введи числа!")
        cur.close()
        conn.close()
        return

    cur.execute("""
        UPDATE Product 
        SET Stock_Quantity = %s 
        WHERE Product_ID = %s AND Sellers_ID = %s
        RETURNING Product_Name
    """, (new_stock, product_id, current_seller['id']))

    result = cur.fetchone()

    if result:
        conn.commit()
        print(Fore.GREEN + f"✅ Остаток товара '{result[0]}' обновлён: {new_stock} шт.")
    else:
        print(Fore.RED + "❌ Товар не найден или не принадлежит вам")

    cur.close()
    conn.close()


def show_seller_orders():
    """Просмотр заказов с товарами продавца"""
    global current_seller

    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT
            o.Order_ID,
            o.Order_Date,
            o.Status,
            c.Full_Name,
            SUM(oi.Quantity * oi.Price_At_Time) AS Order_Total
        FROM Orders o
        JOIN Orders_Item oi ON o.Order_ID = oi.Order_ID
        JOIN Product p ON oi.Product_ID = p.Product_ID
        JOIN Customers c ON o.Customer_ID = c.Customer_ID
        WHERE p.Sellers_ID = %s
        GROUP BY o.Order_ID, o.Order_Date, o.Status, c.Full_Name
        ORDER BY o.Order_Date DESC
    """, (current_seller['id'],))

    orders = cur.fetchall()

    if not orders:
        print(Fore.YELLOW + "\n📭 У вас пока нет заказов")
        cur.close()
        conn.close()
        return

    print(Fore.CYAN + Style.BRIGHT + f"\n📋 ЗАКАЗЫ С МОИМИ ТОВАРАМИ")

    for order in orders:
        order_id, order_date, status, customer, total = order

        print(Fore.YELLOW + Style.BRIGHT + f"\n🛍️ Заказ №{order_id} от {order_date}")
        print(Fore.WHITE + f"   Покупатель: {customer}")
        print(Fore.WHITE + f"   Статус: {status} | Сумма заказа: {total} ₽")

        cur.execute("""
            SELECT 
                p.Product_Name,
                oi.Quantity,
                oi.Price_At_Time
            FROM Orders_Item oi
            JOIN Product p ON oi.Product_ID = p.Product_ID
            WHERE oi.Order_ID = %s AND p.Sellers_ID = %s
        """, (order_id, current_seller['id']))

        items = cur.fetchall()

        print(Fore.CYAN + "   📦 Мои товары в заказе:")
        for item in items:
            product_name, qty, price = item
            print(Fore.WHITE + f"      • {product_name} x {qty} = {price * qty} ₽")

    cur.close()
    conn.close()


def seller_menu():
    """Меню продавца"""
    global current_seller

    while True:
        print(Fore.MAGENTA + Style.BRIGHT + "\n" + "=" * 50)
        print(Fore.MAGENTA + Style.BRIGHT + f" 🏪 ZONIK SELLER | {current_seller['store_name']}")
        print(Fore.MAGENTA + Style.BRIGHT + "=" * 50)
        print(Fore.WHITE + "1. ➕ Добавить товар")
        print(Fore.WHITE + "2. 📦 Мои товары")
        print(Fore.WHITE + "3. 🔄 Обновить остатки")
        print(Fore.WHITE + "4. 📋 Заказы с моими товарами")
        print(Fore.WHITE + "5. 📊 Топ товаров (общая аналитика)")
        print(Fore.WHITE + "6. 🚪 Выйти из аккаунта")
        print(Fore.WHITE + "7. ❌ Выход из программы")
        print(Fore.MAGENTA + "-" * 50)

        choice = input(Fore.YELLOW + "Выбери (1-7): ")

        if choice == '1':
            add_product()
        elif choice == '2':
            show_my_products()
        elif choice == '3':
            update_stock()
        elif choice == '4':
            show_seller_orders()
        elif choice == '5':
            show_analytics()
        elif choice == '6':
            logout()
            return
        elif choice == '7':
            print(Fore.CYAN + "\n👋 До встречи в Zonik!")
            exit()
        else:
            print(Fore.RED + "❌ Неверный выбор")


# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Главная функция запуска"""
    while True:
        role = login_menu()

        if role == 'customer':
            customer_menu()
        elif role == 'seller':
            seller_menu()
        elif role is None:
            break


if __name__ == "__main__":
    main()
