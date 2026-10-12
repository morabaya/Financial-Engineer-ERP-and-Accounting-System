from app.models.financials import JournalEntry, JournalEntryLine
from app.models.inventory import Item, Warehouse, StockMovement
from app.services.accounting_engine import create_accounting_entry
from sqlalchemy.orm import Session

class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def update_stock(self, item_id, warehouse_id, quantity, m_type, ref_no=None, user_id=1):
        # 1. Record Movement
        movement = StockMovement(
            item_id=item_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            movement_type=m_type,
            reference_no=ref_no,
            user_id=user_id
        )
        self.db.add(movement)
        
        # 2. Update Item Current Stock
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if item:
            item.current_stock += quantity
        
        self.db.commit()
        
        # 3. Financial Impact (COGS)
        # If it's a sale, we should increase COGS and decrease Inventory Asset
        if m_type == 'Sale' and item:
            cost = item.purchase_price * abs(quantity)
            lines = [
                {'account_id': 51, 'debit': cost, 'credit': 0}, # COGS Account
                {'account_id': 113, 'debit': 0, 'credit': cost} # Inventory Asset Account
            ]
            create_accounting_entry(self.db, f"Stock Out: {ref_no}", ref_no, lines)
            self.db.commit()
        
        return movement.id

    def perform_inventory_count(self, item_id, warehouse_id, actual_qty, user_id=1):
        item = self.db.query(Item).filter(Item.id == item_id).first()
        diff = actual_qty - item.current_stock
        
        if diff != 0:
            self.update_stock(item_id, warehouse_id, diff, 'Adjustment', user_id=user_id)
            
        return diff
