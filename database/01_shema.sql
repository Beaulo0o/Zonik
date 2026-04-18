create table public.category (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  categories_id integer primary key not null default nextval('category_categories_id_seq'::regclass),
  category_name character varying(30) not null
);

create table public.customers (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  customer_id integer primary key not null default nextval('customers_customer_id_seq'::regclass),
  full_name character varying(25) not null,
  phone character varying(11) not null,
  email character varying(100),
  address text
);
create unique index customers_phone_key on customers using btree (phone);
create unique index customers_email_key on customers using btree (email);

create table public.delivery (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  delivery_id integer primary key not null default nextval('delivery_delivery_id_seq'::regclass),
  order_id integer,
  delivery_address character varying(50) not null,
  date date not null default CURRENT_DATE,
  delivery_status character varying(30) not null,
  foreign key (order_id) references public.orders (order_id)
  match simple on update no action on delete cascade
);

create table public.orders (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  order_id integer primary key not null default nextval('orders_order_id_seq'::regclass),
  customer_id integer,
  order_date date not null default CURRENT_DATE,
  status character varying(20),
  total_amount numeric(10,2),
  foreign key (customer_id) references public.customers (customer_id)
  match simple on update cascade on delete no action
);
create index idx_orders_customer on orders using btree (customer_id);
create index idx_orders_date on orders using btree (order_date);

create table public.orders_item (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  order_id integer not null,
  product_id integer not null,
  quantity integer,
  price_at_time numeric(10,2),
  primary key (order_id, product_id),
  foreign key (order_id) references public.orders (order_id)
  match simple on update no action on delete cascade,
  foreign key (product_id) references public.product (product_id)
  match simple on update cascade on delete no action
);

create table public.payments (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  payment_id integer primary key not null default nextval('payments_payment_id_seq'::regclass),
  order_id integer,
  payment_method character varying(20) not null,
  date date not null default CURRENT_DATE,
  payment_status character varying(30) not null,
  foreign key (order_id) references public.orders (order_id)
  match simple on update no action on delete cascade
);

create table public.product (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  product_id integer primary key not null default nextval('product_product_id_seq'::regclass),
  product_name character varying(50) not null,
  product_description text,
  price numeric(10,2),
  categories_id integer,
  stock_quantity integer not null,
  sellers_id integer,
  foreign key (categories_id) references public.category (categories_id)
  match simple on update cascade on delete no action,
  foreign key (sellers_id) references public.sellers (sellers_id)
  match simple on update no action on delete cascade
);
create index idx_product_category on product using btree (categories_id);
create index idx_product_seller on product using btree (sellers_id);

create table public.sellers (
  tableoid oid not null,
  cmax cid not null,
  xmax xid not null,
  cmin cid not null,
  xmin xid not null,
  ctid tid not null,
  sellers_id integer primary key not null default nextval('sellers_sellers_id_seq'::regclass),
  store_name character varying(50) not null,
  contact character varying(50),
  rating numeric(3,2)
);
