-- =============================================
-- ZONIK MARKETPLACE - FUNCTIONS & TRIGGERS
-- Версия: 1.0.0
-- =============================================

-- =============================================
-- 1. ФУНКЦИЯ: Проверка остатка перед добавлением в заказ
-- =============================================
CREATE OR REPLACE FUNCTION check_stock_before_order()
RETURNS TRIGGER AS $$
DECLARE
    available_stock INT;
BEGIN
    SELECT Stock_Quantity INTO available_stock
    FROM Product
    WHERE Product_ID = NEW.Product_ID;

    IF available_stock < NEW.Quantity THEN
        RAISE EXCEPTION 'Недостаточно товара на складе. Доступно: %, запрошено: %',
                        available_stock, NEW.Quantity;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_stock ON Orders_Item;
CREATE TRIGGER trg_check_stock
BEFORE INSERT ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION check_stock_before_order();

-- =============================================
-- 2. ФУНКЦИЯ: Автоматическое списание остатков при заказе
-- =============================================
CREATE OR REPLACE FUNCTION update_stock_after_order()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Product
    SET Stock_Quantity = Stock_Quantity - NEW.Quantity
    WHERE Product_ID = NEW.Product_ID;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_stock ON Orders_Item;
CREATE TRIGGER trg_update_stock
AFTER INSERT ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION update_stock_after_order();

-- =============================================
-- 3. ФУНКЦИЯ: Возврат остатков при отмене позиции заказа
-- =============================================
CREATE OR REPLACE FUNCTION return_stock_on_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Product
    SET Stock_Quantity = Stock_Quantity + OLD.Quantity
    WHERE Product_ID = OLD.Product_ID;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_return_stock ON Orders_Item;
CREATE TRIGGER trg_return_stock
AFTER DELETE ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION return_stock_on_delete();

-- =============================================
-- 4. ФУНКЦИЯ: Автоматический пересчёт суммы заказа
-- =============================================
CREATE OR REPLACE FUNCTION recalc_order_total()
RETURNS TRIGGER AS $$
DECLARE
    v_order_id INT;
    new_total DECIMAL(10,2);
BEGIN
    -- Определяем ID заказа
    IF TG_OP = 'DELETE' THEN
        v_order_id := OLD.Order_ID;
    ELSE
        v_order_id := NEW.Order_ID;
    END IF;

    -- Пересчитываем сумму
    SELECT COALESCE(SUM(Quantity * Price_At_Time), 0)
    INTO new_total
    FROM Orders_Item
    WHERE Order_ID = v_order_id;

    UPDATE Orders
    SET Total_Amount = new_total
    WHERE Order_ID = v_order_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_recalc_order_total_insert ON Orders_Item;
CREATE TRIGGER trg_recalc_order_total_insert
AFTER INSERT ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION recalc_order_total();

DROP TRIGGER IF EXISTS trg_recalc_order_total_update ON Orders_Item;
CREATE TRIGGER trg_recalc_order_total_update
AFTER UPDATE OF Quantity, Price_At_Time ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION recalc_order_total();

DROP TRIGGER IF EXISTS trg_recalc_order_total_delete ON Orders_Item;
CREATE TRIGGER trg_recalc_order_total_delete
AFTER DELETE ON Orders_Item
FOR EACH ROW
EXECUTE FUNCTION recalc_order_total();

-- =============================================
-- 5. ФУНКЦИЯ: Автоматическая установка даты
-- =============================================
CREATE OR REPLACE FUNCTION set_default_dates()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.Order_Date IS NULL THEN
        NEW.Order_Date := CURRENT_DATE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_order_date ON Orders;
CREATE TRIGGER trg_set_order_date
BEFORE INSERT ON Orders
FOR EACH ROW
EXECUTE FUNCTION set_default_dates();

-- =============================================
-- 6. ХРАНИМАЯ ПРОЦЕДУРА: Полное создание заказа
-- =============================================
CREATE OR REPLACE PROCEDURE create_order_full(
    p_customer_id INT,
    p_product_ids INT[],
    p_quantities INT[],
    p_payment_method VARCHAR DEFAULT 'При получении',
    p_delivery_address VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INT;
    v_price DECIMAL(10,2);
    v_address VARCHAR;
    i INT;
BEGIN
    -- Получаем адрес доставки
    IF p_delivery_address IS NULL THEN
        SELECT Address INTO v_address
        FROM Customers
        WHERE Customer_ID = p_customer_id;
    ELSE
        v_address := p_delivery_address;
    END IF;

    -- Создаём заказ (сумма пока 0, триггер пересчитает)
    INSERT INTO Orders (Customer_ID, Status, Total_Amount)
    VALUES (p_customer_id, 'Ожидает', 0)
    RETURNING Order_ID INTO v_order_id;

    -- Добавляем позиции (триггеры спишут остатки и пересчитают сумму)
    FOR i IN 1..array_length(p_product_ids, 1)
    LOOP
        SELECT Price INTO v_price
        FROM Product
        WHERE Product_ID = p_product_ids[i];

        INSERT INTO Orders_Item (Order_ID, Product_ID, Quantity, Price_At_Time)
        VALUES (v_order_id, p_product_ids[i], p_quantities[i], v_price);
    END LOOP;

    -- Добавляем оплату
    INSERT INTO Payments (Order_ID, Payment_Method, Payment_Status)
    VALUES (v_order_id, p_payment_method, 'Ожидает');

    -- Добавляем доставку
    INSERT INTO Delivery (Order_ID, Delivery_Address, Delivery_Status)
    VALUES (v_order_id, v_address, 'Ожидает');

    RAISE NOTICE 'Заказ #% создан и оплачен', v_order_id;
END;
$$;

-- =============================================
-- 7. ФУНКЦИЯ: Статистика по продавцу
-- =============================================
CREATE OR REPLACE FUNCTION get_seller_stats(p_seller_id INT)
RETURNS TABLE (
    total_products INT,
    total_sold BIGINT,
    total_revenue NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT p.Product_ID)::INT,
        COALESCE(SUM(oi.Quantity), 0),
        COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0)
    FROM Product p
    LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
    WHERE p.Sellers_ID = p_seller_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ПРОВЕРКА РАБОТЫ
-- =============================================
-- SELECT * FROM information_schema.triggers WHERE trigger_schema = 'public';