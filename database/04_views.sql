-- =============================================
-- ZONIK MARKETPLACE - VIEWS (ПРЕДСТАВЛЕНИЯ)
-- Версия: 1.0.0
-- =============================================

-- Представление: Полная информация о товарах с продавцами и категориями
CREATE OR REPLACE VIEW v_product_full AS
SELECT
    p.Product_ID,
    p.Product_Name,
    p.Product_Description,
    p.Price,
    p.Stock_Quantity,
    c.Category_Name,
    s.Store_Name AS Seller_Name,
    s.Rating AS Seller_Rating,
    CASE
        WHEN p.Stock_Quantity = 0 THEN 'Нет в наличии'
        WHEN p.Stock_Quantity < 5 THEN 'Заканчивается'
        ELSE 'В наличии'
    END AS Availability
FROM Product p
JOIN Category c ON p.Categories_ID = c.Categories_ID
JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID;

-- Представление: Детали заказов с покупателями и статусами
CREATE OR REPLACE VIEW v_orders_full AS
SELECT
    o.Order_ID,
    o.Order_Date,
    o.Status AS Order_Status,
    o.Total_Amount,
    c.Full_Name AS Customer_Name,
    c.Phone AS Customer_Phone,
    p.Payment_Method,
    p.Payment_Status,
    d.Delivery_Address,
    d.Delivery_Status
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
LEFT JOIN Payments p ON o.Order_ID = p.Order_ID
LEFT JOIN Delivery d ON o.Order_ID = d.Order_ID;

-- Представление: Статистика по продавцам
CREATE OR REPLACE VIEW v_seller_stats AS
SELECT
    s.Sellers_ID,
    s.Store_Name,
    s.Rating,
    COUNT(DISTINCT p.Product_ID) AS Total_Products,
    COALESCE(SUM(oi.Quantity), 0) AS Total_Sold,
    COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0) AS Total_Revenue,
    COUNT(DISTINCT o.Order_ID) AS Total_Orders
FROM Sellers s
LEFT JOIN Product p ON s.Sellers_ID = p.Sellers_ID
LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
LEFT JOIN Orders o ON oi.Order_ID = o.Order_ID
GROUP BY s.Sellers_ID, s.Store_Name, s.Rating
ORDER BY Total_Revenue DESC;

-- Представление: Корзина (активные заказы со статусом 'Ожидает')
CREATE OR REPLACE VIEW v_active_carts AS
SELECT
    o.Order_ID,
    o.Customer_ID,
    c.Full_Name,
    o.Order_Date,
    COUNT(oi.Product_ID) AS Items_Count,
    o.Total_Amount
FROM Orders o
JOIN Customers c ON o.Customer_ID = c.Customer_ID
JOIN Orders_Item oi ON o.Order_ID = oi.Order_ID
WHERE o.Status = 'Ожидает'
GROUP BY o.Order_ID, o.Customer_ID, c.Full_Name, o.Order_Date, o.Total_Amount;

-- Представление: Товары с низким остатком (для закупки)
CREATE OR REPLACE VIEW v_low_stock_products AS
SELECT
    p.Product_ID,
    p.Product_Name,
    p.Stock_Quantity,
    s.Store_Name,
    s.Contact AS Seller_Contact,
    c.Category_Name
FROM Product p
JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
JOIN Category c ON p.Categories_ID = c.Categories_ID
WHERE p.Stock_Quantity < 5
ORDER BY p.Stock_Quantity ASC;

-- Представление: Ежедневная выручка
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT
    o.Order_Date,
    COUNT(DISTINCT o.Order_ID) AS Orders_Count,
    SUM(o.Total_Amount) AS Daily_Revenue,
    AVG(o.Total_Amount) AS Avg_Order_Value
FROM Orders o
WHERE o.Status != 'Отменён'
GROUP BY o.Order_Date
ORDER BY o.Order_Date DESC;