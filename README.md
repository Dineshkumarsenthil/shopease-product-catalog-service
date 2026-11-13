# ShopEase Product Catalog Service

Independent microservice for products, categories and inventory. Built with FastAPI, SQLAlchemy, Alembic and MySQL 8, and runs in Docker. It has its own database (`shopease_product_catalog_db`) and does not handle login. It only checks JWT tokens issued by the Authentication Service.

## Folder structure
```
app/
  main.py          app and router setup
  routers/         API endpoints (product, category, inventory)
  schemas/         Pydantic request/response models
  models/          SQLAlchemy tables
  services/        business logic
  core/            config.py (settings), security.py (JWT checks)
  database/        engine and session
alembic/           migrations
scripts/           concurrent stock test
```

## Database schema
| Table | Main columns |
|---|---|
| categories | id, name (unique), description, is_active, created_at, updated_at |
| products | id, category_id (FK), name, description, sku (unique), price, discount_price, stock_quantity, image_url, brand, is_active, created_at, updated_at |
| inventory_transactions | id, product_id (FK), transaction_type (IN/OUT), quantity, previous_stock, updated_stock, remarks, created_at |

Constraints: unique SKU, unique category name, `price >= 0`, `stock_quantity >= 0`, `discount_price <= price`. Prices use `DECIMAL(10,2)`.

## Environment variables (.env)
Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

| Variable | Meaning |
|---|---|
| MYSQL_HOST / MYSQL_PORT | Database host and port (Compose sets these inside Docker) |
| MYSQL_ROOT_PASSWORD | MySQL root password |
| MYSQL_DATABASE | shopease_product_catalog_db |
| JWT_SECRET_KEY | Must be the same secret the Auth Service signs with |
| JWT_ALGORITHM | Same algorithm as the Auth Service (HS256) |
| JWT_USER_ID_CLAIM / JWT_ROLE_CLAIM | Token claim names for user id and role (`sub`, `role`) |
| ADMIN_ROLE | Role value that counts as administrator (`admin`) |
| LOW_STOCK_THRESHOLD | Default low-stock limit (10) |

## Run with Docker
```
docker compose up --build -d
docker compose ps
docker compose logs product-catalog-service
```
Swagger UI: http://localhost:8003/docs  (MySQL is on host port 3309.)
Migrations run automatically before the app starts.

## Alembic commands
```
docker compose exec product-catalog-service alembic upgrade head
docker compose exec product-catalog-service alembic current
docker compose exec product-catalog-service alembic revision --autogenerate -m "message"
```

## JWT authentication
Send `Authorization: Bearer <token>` with every request. The token comes from the Auth Service login.
- Missing or invalid/expired token: **401**
- Valid token but not an admin on an admin API: **403**
- Admins: create, update and delete products and categories, and use all inventory APIs.
- Customers: view active products and active categories only.

## API endpoints
| Method | Endpoint | Access |
|---|---|---|
| POST | /api/categories/ | Admin |
| GET | /api/categories/ , /api/categories/{id} | Any logged-in user |
| PUT, DELETE | /api/categories/{id} | Admin |
| POST | /api/products/ | Admin |
| GET | /api/products/ , /api/products/{id} | Any logged-in user |
| PUT, PATCH, DELETE | /api/products/{id} | Admin |
| GET | /api/inventory/{id} | Admin |
| POST | /api/inventory/{id}/stock-in , /stock-out | Admin |
| GET | /api/inventory/{id}/history | Admin |
| GET | /api/inventory/low-stock | Admin |

Business rules:
- Product SKU and category name must be unique (409 if repeated).
- A product needs an existing category (404 if not).
- A category that still has products cannot be deleted (409). Move or delete the products first, or deactivate the category.
- Deleting a product also deletes its stock history. To hide a product without deleting it, set `is_active` to false.
- Customers never see inactive products, or products in an inactive category. Admins can add `include_inactive=true`.
- Stock is changed only through the inventory APIs. PUT/PATCH on a product do not change stock.

## Search, filter, pagination and sorting
```
GET /api/products/?search=mobile
GET /api/products/?category_id=1
GET /api/products/?min_price=1000&max_price=5000
GET /api/products/?in_stock=true
GET /api/products/?page=1&page_size=10
GET /api/products/?sort_by=price&sort_order=asc
```
`sort_by` can be id, name, price, stock_quantity or created_at. `page_size` is at most 100.

## Inventory workflow
1. Create a product with an opening stock (this is saved as the first "IN" record).
2. Use `stock-in` to add stock and `stock-out` to remove stock. Quantity must be greater than 0.
3. Every change saves the previous and updated stock in `inventory_transactions`.
4. The product row is locked (`SELECT ... FOR UPDATE`) while it is updated, so simultaneous requests cannot corrupt the count. The stock update and the history record are saved in one transaction and rolled back together on any error.
5. A stock-out larger than the available stock returns 400 and changes nothing.
6. `low-stock` lists active products at or below the threshold.

## Concurrency test
Set a product's stock to 20, then run:
```
python scripts/concurrent_stock_test.py <admin_token> <product_id>
```
Expected result: 20 successful, 10 rejected, final stock 0.
