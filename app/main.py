from fastapi import FastAPI

from app.routers import category_routes, inventory_routes, product_routes

app = FastAPI(
    title="ShopEase Product Catalog Service",
    description="Products, categories and inventory management",
    version="1.0.0",
)

app.include_router(category_routes.router)
app.include_router(product_routes.router)
app.include_router(inventory_routes.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "product-catalog-service"}
