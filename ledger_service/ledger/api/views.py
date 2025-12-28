from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import *
from rest_framework.exceptions import AuthenticationFailed
from .serializers import *
from django.db import transaction as db_transaction
from rest_framework import status
from ..tasks import *
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


"""
class create_ledgerAccount(APIView):
    def post(self, request):
        serializer = LedgerAccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            return Response(LedgerAccountSerializer(account).data, status=201)
        return Response(serializer.errors, status=400)
 """   
 
class create_ledgerAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """
    API endpoint to create a new LedgerAccount entry.
    Requires external_account_id and user_id UUIDs in the request body.
    """
    def post(self, request, *args, **kwargs):
        # Use the serializer to validate and save the data
        serializer = LedgerAccountSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # In a real app: account = serializer.save()
                # Using mock create for demonstration:
                account = LedgerAccount.objects_create(**serializer.validated_data)
                
                print(f"[Ledger] Successfully created account: {account.id}")
                
                data = {
                    "account_id": str(account.id),
                    "external_id": str(account.external_account_id),
                    "created_at": account.created_at.isoformat(),
                }
                publish_ledgerAccount_created.apply_async(args=[data])
                return Response({"id": str(account.id), **serializer.data},
                                status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"[ERROR] Database save failed: {e}")
                return Response(
                    {"error": "Could not create LedgerAccount.", "details": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class create_ledgerEntry(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LedgerEntrySerializer(data=request.data)
        if serializer.is_valid():
            entry = serializer.save()
            
            data = {
                "id": str(entry.id),
                "transaction": str(entry.txn),
                "ledger_account": str(entry.payer_account),
                "entry_type": str(entry.entry_type),
                "amount": str(entry.amount),
                "currency": str(entry.currency),
                "created_at": entry.created_at.isoformat(),
            }
            publish_ledgerEntry_created.apply_async(args=[data])
            return Response({"message": "Ledger Entry successfully created",
                             "entry": entry}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class create_transaction(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @db_transaction.atomic
    def post(self, request):
        """
        Required fields:
        - reference (unique)
        - description
        - debit_account
        - credit_account
        - amount
        """
        data = request.data

        # Idempotency: If transaction exists, return it
        if Transaction.objects.filter(reference=data["reference"]).exists():
            txn = Transaction.objects.get(reference=data["reference"])
            return Response(TransactionSerializer(txn).data, status=200)

        # Create transaction
        txn = Transaction.objects.create(
            reference=data["reference"],
            description=data.get("description", "")
        )

        amount = data["amount"]
        debit_account = LedgerAccount.objects.get(id=data["debit_account"])
        credit_account = LedgerAccount.objects.get(id=data["credit_account"])

        # Create DEBIT entry
        LedgerEntry.objects.create(
            transaction=txn,
            account=debit_account,
            entry_type="DEBIT",
            amount=amount
        )

        # Create CREDIT entry
        LedgerEntry.objects.create(
            transaction=txn,
            account=credit_account,
            entry_type="CREDIT",
            amount=amount
        )   
        data =   {          
            "id": str(txn.id),
            "reference": txn.reference,
            "description": txn.description,
            "created_at": txn.created_at.isoformat(),
            "reconciled": txn.is_reconciled,
        }
        publish_transaction_created.apply_async(args=[data])
        return Response(TransactionSerializer(txn).data, status=201)
    

class BankLogs(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        credit_history = []
        debit_history = []
        
        credits = LedgerEntry.objects.filter(entry_type='CREDIT').all()
        debits = LedgerEntry.objects.filter(entry_type='DEBIT').all()
        
        for credit in credits:
            credit_data = {
                'amount': credit.amount,
                'currency': credit.currency,
                'created_at': credit.created_at,
                'transaction_id': credit.transaction_id,
            }
            credit_history.append(credit_data)
            
        for debit in debits:
            debit_data = {
                'amount': debit.amount,
                'currency': debit.currency,
                'created_at': debit.created_at,
                'transaction_id': debit.transaction_id,
            }
            debit_history.append(debit_data)
            
        return Response({"message": "Successfully Retrieved the data",
                         "credit_data": credit_history, "debit_data": debit_history},
                        status=200)
        

    