-- =============================================
-- ZONIK MARKETPLACE - ANALYTICS QUERIES
-- Версия: 1.0.0
-- =============================================

-- 1. ТОП-10 ТОВАРОВ ПО ВЫРУЧКЕ
SELECT
    p.Product_Name,
    s.Store_Name,
    COALESCE(SUM(oi.Quantity), 0) AS Total_Sold,
    COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0) AS Revenue
FROM Product p
JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
GROUP BY p.Product_ID, p.Product_Name, s.Store_Name
ORDER BY Revenue DESC
LIMIT 10;

-- 2. ТОП-5 ПОКУПАТЕЛЕЙ ПО СУММЕ ЗАКАЗОВ
SELECT
    c.Full_Name,
    c.Phone,
    COUNT(o.Order_ID) AS Orders_Count,
    SUM(o.Total_Amount) AS Total_Spent
FROM Customers c
JOIN Orders o ON c.Customer_ID = o.Customer_ID
WHERE o.Status != 'Отменён'
GROUP BY c.Customer_ID, c.Full_Name, c.Phone
ORDER BY Total_Spent DESC
LIMIT 5;

-- 3. САМЫЕ ПОПУЛЯРНЫЕ КАТЕГОРИИ
SELECT
    cat.Category_Name,
    COUNT(DISTINCT p.Product_ID) AS Products_Count,
    COALESCE(SUM(oi.Quantity), 0) AS Items_Sold,
    COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0) AS Revenue
FROM Category cat
LEFT JOIN Product p ON cat.Categories_ID = p.Categories_ID
LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
GROUP BY cat.Categories_ID, cat.Category_Name
ORDER BY Revenue DESC;

-- 4. СРЕДНИЙ ЧЕК ПО МЕСЯЦАМ
SELECT
    TO_CHAR(Order_Date, 'YYYY-MM') AS Month,
    COUNT(*) AS Orders_Count,
    ROUND(AVG(Total_Amount), 2) AS Avg_Check,
    SUM(Total_Amount) AS Total_Revenue
FROM Orders
WHERE Status != 'Отменён'
GROUP BY TO_CHAR(Order_Date, 'YYYY-MM')
ORDER BY Month DESC;

-- 5. КОНВЕРСИЯ СПОСОБОВ ОПЛАТЫ
SELECT
    Payment_Method,
    COUNT(*) AS Usage_Count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Percentage
FROM Payments
GROUP BY Payment_Method
ORDER BY Usage_Count DESC;

-- 6. ТОВАРЫ, КОТОРЫЕ НИ РАЗУ НЕ ЗАКАЗЫВАЛИ (НЕЛИКВИД)
SELECT
    p.Product_ID,
    p.Product_Name,
    s.Store_Name,
    p.Stock_Quantity,
    p.Price
FROM Product p
JOIN Sellers s ON p.Sellers_ID = s.Sellers_ID
LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
WHERE oi.Product_ID IS NULL
ORDER BY p.Stock_Quantity DESC;

-- 7. СТАТИСТИКА ПО СТАТУСАМ ЗАКАЗОВ
SELECT
    Status,
    COUNT(*) AS Count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Percentage,
    SUM(Total_Amount) AS Total_Value
FROM Orders
GROUP BY Status
ORDER BY Count DESC;

-- 8. ABC-АНАЛИЗ ТОВАРОВ (по выручке)
WITH product_revenue AS (
    SELECT
        p.Product_ID,
        p.Product_Name,
        COALESCE(SUM(oi.Quantity * oi.Price_At_Time), 0) AS Revenue
    FROM Product p
    LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
    GROUP BY p.Product_ID, p.Product_Name
),
ranked AS (
    SELECT
        Product_Name,
        Revenue,
        SUM(Revenue) OVER (ORDER BY Revenue DESC) * 100.0 / SUM(Revenue) OVER () AS Cumulative_Percent
    FROM product_revenue
    WHERE Revenue > 0
)
SELECT
    Product_Name,
    ROUND(Revenue, 2) AS Revenue,
    ROUND(Cumulative_Percent, 1) AS Cumulative_Percent,
    CASE
        WHEN Cumulative_Percent <= 80 THEN 'A (Топ)'
        WHEN Cumulative_Percent <= 95 THEN 'B (Средние)'
        ELSE 'C (Низкие)'
    END AS ABC_Category
FROM ranked
ORDER BY Revenue DESC;

-- 9. ВЫРУЧКА ПО ПРОДАВЦАМ С РЕЙТИНГОМ
SELECT
    s.Store_Name,
    s.Rating,
    COUNT(DISTINCT o.Order_ID) AS Orders_Count,
    COALESCE(SUM(o.Total_Amount), 0) AS Revenue,
    CASE
        WHEN s.Rating >= 4.5 THEN '🌟 Премиум'
        WHEN s.Rating >= 4.0 THEN '✅ Надёжный'
        WHEN s.Rating >= 3.0 THEN '👌 Средний'
        ELSE '⚠️ Низкий рейтинг'
    END AS Seller_Status
FROM Sellers s
LEFT JOIN Product p ON s.Sellers_ID = p.Sellers_ID
LEFT JOIN Orders_Item oi ON p.Product_ID = oi.Product_ID
LEFT JOIN Orders o ON oi.Order_ID = o.Order_ID
GROUP BY s.Sellers_ID, s.Store_Name, s.Rating
ORDER BY Revenue DESC;

-- 10. ДИНАМИКА ПРОДАЖ ЗА ПОСЛЕДНИЕ 7 ДНЕЙ
SELECT
    Order_Date,
    COUNT(*) AS Orders_Count,
    SUM(Total_Amount) AS Daily_Revenue
FROM Orders
WHERE Order_Date >= CURRENT_DATE - INTERVAL '7 days'
  AND Status != 'Отменён'
GROUP BY Order_Date
ORDER BY Order_Date DESC;

-- 11. САМЫЕ АКТИВНЫЕ ДНИ НЕДЕЛИ
SELECT
    TO_CHAR(Order_Date, 'Day') AS Weekday,
    COUNT(*) AS Orders_Count,
    ROUND(AVG(Total_Amount), 2) AS Avg_Check
FROM Orders
GROUP BY TO_CHAR(Order_Date, 'Day'), EXTRACT(DOW FROM Order_Date)
ORDER BY EXTRACT(DOW FROM Order_Date);

-- 12. КЛИЕНТЫ, КОТОРЫЕ НЕ ДЕЛАЛИ ЗАКАЗЫ БОЛЕЕ 30 ДНЕЙ
SELECT
    c.Customer_ID,
    c.Full_Name,
    c.Phone,
    MAX(o.Order_Date) AS Last_Order_Date,
    CURRENT_DATE - MAX(o.Order_Date) AS Days_Since_Last_Order
FROM Customers c
JOIN Orders o ON c.Customer_ID = o.Customer_ID
GROUP BY c.Customer_ID, c.Full_Name, c.Phone
HAVING MAX(o.Order_Date) < CURRENT_DATE - INTERVAL '30 days'
ORDER BY Days_Since_Last_Order DESC;