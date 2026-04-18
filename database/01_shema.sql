-- Очищенная версия (без tableoid, cmax, xmax и т.д.)
CREATE TABLE Customers (
    Customer_ID SERIAL PRIMARY KEY,
    Full_Name VARCHAR(25) NOT NULL,
    Phone VARCHAR(11) NOT NULL UNIQUE,
    Email VARCHAR(100) UNIQUE,
    Address TEXT
);

CREATE TABLE Sellers (
    Sellers_ID SERIAL PRIMARY KEY,
    Store_Name VARCHAR(50) NOT NULL,
    Contact VARCHAR(50),
    Rating DECIMAL(3,2) CHECK (Rating BETWEEN 0 AND 5)
);

CREATE TABLE Category (
    Categories_ID SERIAL PRIMARY KEY,
    Category_Name VARCHAR(30) NOT NULL
);

CREATE TABLE Product (
    Product_ID SERIAL PRIMARY KEY,
    Product_Name VARCHAR(50) NOT NULL,
    Product_Description TEXT,
    Price DECIMAL(10,2),
    Categories_ID INT REFERENCES Category(Categories_ID) ON UPDATE CASCADE,
    Stock_Quantity INT NOT NULL CHECK (Stock_Quantity >= 0),
    Sellers_ID INT REFERENCES Sellers(Sellers_ID) ON DELETE CASCADE
);

CREATE TABLE Orders (
    Order_ID SERIAL PRIMARY KEY,
    Customer_ID INT REFERENCES Customers(Customer_ID) ON UPDATE CASCADE,
    Order_Date DATE NOT NULL DEFAULT CURRENT_DATE,
    Status VARCHAR(20),
    Total_Amount DECIMAL(10,2)
);

CREATE TABLE Orders_Item (
    Order_ID INT REFERENCES Orders(Order_ID) ON DELETE CASCADE,
    Product_ID INT REFERENCES Product(Product_ID) ON UPDATE CASCADE,
    Quantity INT,
    Price_At_Time DECIMAL(10,2),
    PRIMARY KEY (Order_ID, Product_ID)
);

CREATE TABLE Payments (
    Payment_ID SERIAL PRIMARY KEY,
    Order_ID INT REFERENCES Orders(Order_ID) ON DELETE CASCADE,
    Payment_Method VARCHAR(20) NOT NULL CHECK (Payment_Method IN ('При получении', 'Картой онлайн', 'СБП')),
    Date DATE NOT NULL DEFAULT CURRENT_DATE,
    Payment_Status VARCHAR(30) NOT NULL CHECK (Payment_Status IN ('Ожидает', 'Оплачено', 'Отменено'))
);

CREATE TABLE Delivery (
    Delivery_ID SERIAL PRIMARY KEY,
    Order_ID INT REFERENCES Orders(Order_ID) ON DELETE CASCADE,
    Delivery_Address VARCHAR(50) NOT NULL,
    Date DATE NOT NULL DEFAULT CURRENT_DATE,
    Delivery_Status VARCHAR(30) NOT NULL CHECK (Delivery_Status IN ('Ожидает', 'В пути', 'Доставлен', 'Отменен'))
);
