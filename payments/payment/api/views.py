from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import *
from .serializers import *
from django.db import transaction 
from ..tasks import *
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q

import time # <--- Import this

class InternalTransferAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        acc = get_object_or_404(PaymentAccount, user_id=user_id)
        payer_account_id = acc.account_number
        serializer = PaymentCreateSerializer(data=request.data)
        # 1. START THE CLOCK
        start_time = time.time() 
        
        if serializer.is_valid():
            with transaction.atomic():
                # Construct a clean dictionary to send to Celery
                payment_req = PaymentRequest.objects.create(
                    payer_account_id=payer_account_id,
                    payee_account_id=serializer.validated_data['payee_account_id'],
                    amount=serializer.validated_data['amount'],
                    status="PENDING",
                    currency = "NGN",
                    payment_type="INTERNAL_TRANSFER",
                    # Store the task ID if needed later
                )
                data = {
                    "payment_id": payment_req.id,
                    "user_id": str(user_id),
                    "payer_account_id": payer_account_id,
                    "payee_account_id": serializer.validated_data['payee_account_id'],
                    "amount": str(serializer.validated_data['amount']), # Use String for currency!
                    #"account_type": str(serializer.validated_data['account_type']),
                    "pin": str(serializer.validated_data['pin']), # Lowercase 'pin'
                    # 2. ADD TIMESTAMP TO PAYLOAD
                    "initiated_at_ts": start_time
                }
                
                # Fire and forget
                transaction.on_commit(lambda: process_internal_transfer.apply_async(args=[data]))

                return Response({"status": "Processing",}, status=200)
        else:
            return Response(serializer.errors, status=400)

class CardPaymentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CardPaymentSerializer(data=request.data)
        user_id = request.user.id
        acc = get_object_or_404(PaymentAccount, user_id=user_id)
        payer_account_id = acc.account_number
         # 1. START THE CLOCK
        start_time = time.time() 
        
        if serializer.is_valid():
            with transaction.atomic():
                
                # Create the Pending Transaction Record HERE (Before Celery)
                # This ensures you have a record even if Celery crashes immediately
                payment_req = PaymentRequest.objects.create(
                    payer_account_id = payer_account_id,
                    payee_account_id = serializer.validated_data['payee_account_id'],
                    amount=serializer.validated_data['amount'],
                    currency = "NGN",
                    status = "PENDING",
                    payment_type = "CARD",
                    # Store the task ID if needed later
                )
                data = {
                    "payment_id": payment_req.id,
                    "user_id": str(user_id),
                    "payer_account_id": payer_account_id,
                    "payee_account_id": serializer.validated_data['payee_account_id'],
                    "amount": str(serializer.validated_data['amount']), # Use String for currency!
                    "PIN": str(serializer.validated_data['pin']),
                    "card_number": str(serializer.validated_data['card_number']),
                    "cvv": str(serializer.validated_data['cvv']),
                    # 2. ADD TIMESTAMP TO PAYLOAD
                    "initiated_at_ts": start_time
                }
                
                transaction.on_commit(lambda: initiate_card_payment.apply_async(args=[data], queue='payment.internal'))
        
                return Response({"status": "Processing"}, status=200)
        else:
            return Response(serializer.errors, status=400)


class TransferHistory(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.user.id 
        acc = get_object_or_404(PaymentAccount, user_id=user_id)
        number = acc.account_number
        payments = PaymentRequest.objects.order_by('-created_at')

        history_data = [] 

        for payment in payments:
            data = {
                'sender': payment.payer_account_id,
                'recipient': payment.payee_account_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'payment_type': payment.payment_type,
                'date': payment.created_at,
                'status': payment.status,
            }

            history_data.append(data)
        
        return Response({"message": "Your transfer History", "data": history_data}, 
                        status=200)

class GeneralTransferHistory(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = PaymentRequest.objects.order_by('-created_at')
    
        history_data = [] 

        for payment in payments:
            data = {
                'sender': payment.payer_account_id,
                'recipient': payment.payee_account_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'payment_type': payment.payment_type,
                'date': payment.created_at,
                'status': payment.status,
            }
            # 4. Append to the list
            history_data.append(data)
        
        return Response({"message": "Your Bank Transactions History", "data": history_data}, status=200)
    
    
class ExternalBankTransferAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save(payment_type="BANK_EXTERNAL")

        # Trigger external bank API
        #process_external_bank_transfer.apply_async(args=[payment.id])

        return Response(status=201)


