from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import *
from .serializers import *
from django.db import transaction 
from ..tasks import *
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class InternalTransferAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user_id = request.user.id
        acc = get_object_or_404(PaymentAccount, user_id=user_id)
        payer_account_id = acc.account_number
        serializer = PaymentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Construct a clean dictionary to send to Celery
            data = {
                "user_id": str(user_id),
                "payer_account_id": payer_account_id,
                "payee_account_id": serializer.validated_data['payee_account_id'],
                "amount": str(serializer.validated_data['amount']), # Use String for currency!
                "account_type": str(serializer.validated_data['account_type']),
                "pin": str(serializer.validated_data['pin']), # Lowercase 'pin'
            }
            
            # Create the Pending Transaction Record HERE (Before Celery)
            # This ensures you have a record even if Celery crashes immediately
            PaymentRequest.objects.create(
                payer_account_id=payer_account_id,
                payee_account_id=data['payee_account_id'],
                amount=data['amount'],
                status="PENDING",
                currency = "NGN",
                payment_type="INTERNAL_TRANSFER",
                # Store the task ID if needed later
            )
            
            # Fire and forget
            process_internal_transfer.apply_async(args=[data], countdown=2)

            return Response({"status": "Processing", "details": data}, status=201)
        else:
            return Response(serializer.errors, status=400)

class CardPaymentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = CardPaymentSerializer(data=request.data)
        user_id = request.user.id
        acc = get_object_or_404(PaymentAccount, user_id=user_id)
        payer_account_id = acc.account_number
        
        if serializer.is_valid():
            data = {
                "user_id": str(user_id),
                "payer_account_id": payer_account_id,
                "payee_account_id": serializer.validated_data['payee_account_id'],
                "amount": str(serializer.validated_data['amount']), # Use String for currency!
                "PIN": str(serializer.validated_data['PIN']),
                "card_number": str(serializer.validated_data['card_number']),
                "cvv": str(serializer.validated_data['cvv'])
            }
            
            # Create the Pending Transaction Record HERE (Before Celery)
            # This ensures you have a record even if Celery crashes immediately
            PaymentRequest.objects.create(
                payer_account_id = payer_account_id,
                payee_account_id = data['payee_account_id'],
                amount=data['amount'],
                currency = "NGN",
                status = "PENDING",
                payment_type = "CARD",
                # Store the task ID if needed later
            )
            # Create the Pending Transaction Record HERE (Before Celery)
            initiate_card_payment.apply_async(args=[data], queue='payment.internal') #Force the queue here!
    
            return Response({"status": "Processing", "details": data}, status=201)
        else:
            return Response(serializer.errors, status=400)


class ExternalBankTransferAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save(payment_type="BANK_EXTERNAL")

        # Trigger external bank API
        #process_external_bank_transfer.apply_async(args=[payment.id], countdown=10)

        return Response(status=201)


