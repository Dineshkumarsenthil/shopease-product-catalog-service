from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),
        CheckConstraint("updated_stock >= 0", name="ck_inventory_updated_stock_non_negative"),
    )

    id = Column(Integer, primary_key=True)
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type = Column(String(10), nullable=False)  # "IN" or "OUT"
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    updated_stock = Column(Integer, nullable=False)
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    product = relationship("Product", back_populates="transactions")
