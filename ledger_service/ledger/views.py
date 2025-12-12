from decimal import Decimal
from .models import *

# Create your views here.

def get_details(request):
    account_id = request.user
    account = LedgerAccount.objects.get(id=account_id)
    debit_sum = (
        LedgerEntry.objects.filter(account=account, entry_type="DEBIT")
        .aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
    )

    credit_sum = (
        LedgerEntry.objects.filter(account=account, entry_type="CREDIT")
        .aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
    )
    
    return debit_sum, credit_sum