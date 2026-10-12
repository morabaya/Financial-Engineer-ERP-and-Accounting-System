from app.models.financials import JournalEntry, JournalEntryLine
from sqlalchemy.orm import Session

def create_accounting_entry(db: Session, description, reference_no, lines_data, currency="ILS", rate=1.0):
    total_debit = sum(line['debit'] for line in lines_data)
    total_credit = sum(line['credit'] for line in lines_data)
    if abs(total_debit - total_credit) > 0.01:
        raise ValueError(f"القيد غير متوازن! المدين ({total_debit}) != الدائن ({total_credit})")
    entry = JournalEntry(description=description, reference_no=reference_no, currency=currency, exchange_rate=rate)
    db.add(entry)
    db.flush()
    for line in lines_data:
        entry_line = JournalEntryLine(entry_id=entry.id, account_id=line['account_id'], debit=line['debit'], credit=line['credit'])
        db.add(entry_line)
    db.commit()
    return entry.id
