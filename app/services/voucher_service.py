from app.models.financials import JournalEntry, JournalEntryLine
from app.models.vouchers import Voucher, VoucherLine, AuditLog
from app.services.accounting_engine import create_accounting_entry
from sqlalchemy.orm import Session

class VoucherService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_voucher_no(self, v_type):
        prefixes = {'Receipt': 'R', 'Payment': 'P', 'Entry': 'E'}
        prefix = prefixes.get(v_type, 'V')
        last_voucher = self.db.query(Voucher).filter(Voucher.voucher_no.like(f"{prefix}%")).order_by(Voucher.id.desc()).first()
        if not last_voucher:
            return f"{prefix}-0001"
        try:
            last_no = int(last_voucher.voucher_no.split('-')[1])
            return f"{prefix}-{str(last_no + 1).zfill(4)}"
        except:
            return f"{prefix}-0001"

    def create_voucher(self, v_type, description, lines_data, total_amount, currency="ILS", rate=1.0, user_id=1):
        v_no = self._generate_voucher_no(v_type)
        voucher = Voucher(
            voucher_no=v_no,
            type=v_type,
            description=description,
            total_amount=total_amount,
            currency=currency,
            exchange_rate=rate,
            user_id=user_id
        )
        self.db.add(voucher)
        self.db.flush()

        for line in lines_data:
            v_line = VoucherLine(
                voucher_id=voucher.id,
                account_id=line['account_id'],
                debit=line['debit'],
                credit=line['credit']
            )
            self.db.add(v_line)

        accounting_lines = [{'account_id': l['account_id'], 'debit': l['debit'], 'credit': l['credit']} for l in lines_data]
        create_accounting_entry(self.db, description, v_no, accounting_lines, currency, rate)

        audit = AuditLog(
            user_id=user_id,
            action='CREATE',
            table_name='Vouchers',
            record_id=voucher.id,
            new_value=f"Voucher {v_no} created for {total_amount} {currency}"
        )
        self.db.add(audit)
        self.db.commit()
        return voucher.id
