from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password, check_password
from ..models import *
from ..tasks import *
from rest_framework import status
from .serializers import *
from ..generator import *

from ..utils import encrypt_data, decrypt_data



class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Account.objects.all()

    def get(self, request, format=None):
        user_id_value = request.user.id
        account = BankAccount.objects.filter(user_id=user_id_value).first()

        if account is None:
            return Response({}, status=200)
        
        if account.active == False:
            return Response ({'message': 'Account is already blocked.'}, status=status.HTTP_403_FORBIDDEN)
        
        data = {
            'id': account.id,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'account_number': account.account_number,
            'balance': account.balance,
        }
        return Response(data, status=status.HTTP_200_OK)
    

class CreateBankAccount(APIView):
    serializer_class = BankAccountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = BankAccount.objects.all()
    
    def post(self, request, format=None):
        
        user_id = request.user.id
        serializer = BankAccountSerializer(data=request.data)
        if serializer.is_valid():
            if BankAccount.objects.filter(Q(user_id = user_id) & Q(active=True)).exists():
                return Response({'message': 'You already have a current account'}, 
                                status= status.HTTP_409_CONFLICT)

            if BankAccount.objects.filter(Q(user_id = user_id) & Q(active=False)).exists():
                return Response({'message': 'You have an inactive account. Please contact support.'}, status=status.HTTP_403_FORBIDDEN)
            
            hashed_pin_value = make_password(serializer.validated_data["PIN"])
            
            serializer.save(user_id=user_id, PIN=hashed_pin_value, account_number = generate_account_number())
            
            acc_data = get_object_or_404(BankAccount, user_id=user_id)
             
            data = {
                "user_id": acc_data.user_id,
                "account_number": acc_data.account_number,
                "balance": acc_data.balance,
                "interest_rate": acc_data.interest_rate,
                "currency": acc_data.currency,
                "active": acc_data.active, # Assuming this field is appropriate for current account status
                "created_at": acc_data.created_at.isoformat(),
            }
            publish_BankAccount_created.apply_async(args=[data])
            return Response({'message': 'current account created successfully.'}, status=status.HTTP_201_CREATED)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateCard(APIView):
    serializer_class = pinserializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = Card.objects.all()
    
    def post(self, request, format=None):
        user_id = request.user.id
        serializer = pinserializer(data=request.data)
        
        if serializer.is_valid():
            hashed_pin = make_password(str(serializer.validated_data["pin"]))
            
            acc = BankAccount.objects.filter(user_id=user_id).first()
            if acc is None:
                return Response({'message': 'No bank account found for this user.'}, 
                                status=status.HTTP_404_NOT_FOUND)
            
            if Card.objects.filter(user_id=user_id, active=True).exists():  #check if user has an active card
                return Response({'message': 'You already have an active card'}, status=status.HTTP_403_FORBIDDEN)
            
            if Card.objects.filter(user_id=user_id, active=False).exists():  #delete inactive card if it exists
                Card.objects.filter(user_id=user_id, active=False).delete()
            
            Card.objects.create(
                user_id=user_id,
                card_number=encrypt_data(generate_card_number()), # Encrypted Card Number
                cvv=encrypt_data(generate_cvv()),                 # Encrypted CVV
                PIN= hashed_pin,                                  # Hashed Pin
                bank_account=acc,
            )
            
            return Response ({'message': 'Card created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response ({'message': 'Error creating card.'}, status=status.HTTP_400_BAD_REQUEST)


class CreateLoanApplication(APIView):
    serializer_class = LoanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()

    def post(self, request, format=None):
        serializer = LoanSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = request.user.id
            account_number = BankAccount.objects.filter(user_id=user_id).first().account_number
        
            if Loan.objects.filter(user_id=user_id, loan_status__in=["Pending", "approved"]).exists():
                return Response({'message': 'You already have an existing loan or loan application'}, 
                                status= status.HTTP_409_CONFLICT)
            else:
                serializer.save(user_id =user_id, loan_status='pending', account_number=account_number, )
                                       
                return Response({'message': 'Loan application submitted successfully.'},
                            status=status.HTTP_201_CREATED)    
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPendingLoans(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        loans = Loan.objects.filter(loan_status='pending').count()

        return Response(loans, status=200)
    
class GetPendingTickets(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tickets = IT_Tickets.objects.filter(resolved=False).count()
        return Response(tickets, status=200)

class GetAndUpdateLoan(APIView):    #CHECH THISS
    serializer_class = UpdateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()
    
    def get(self, request):
        serializer = GetLoanSerializer(data=request.query_params)
        
        if serializer.is_valid():
            account_number = serializer.validated_data['account_number']
            loan = get_object_or_404(Loan, account_number=account_number)
            
            loan_data = {
                'user_id': loan.user_id,
                'loan_id': loan.loan_id,
                'amount': loan.amount,
                'duration': loan.duration,
                'interest_rate': loan.interest_rate,
                'currency': loan.currency,
                'loan_status': loan.loan_status,
            }
            
            return Response({'message': 'Loan data successfully retrieved.',
                             'data': loan_data},
                            status=status.HTTP_200_OK) 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic  
    def post(self, request, format=None):
        serializer = UpdateLoanSerializer(data=request.data)
        
        if serializer.is_valid():
            account_number = serializer.validated_data['account_number']
            loan_status = serializer.validated_data['status']
            
            loan = get_object_or_404(Loan.objects.select_for_update(), account_number=account_number)
            
            if loan.loan_status.lower() in ['rejected', 'approved']:
                return Response({'message': 'Loan has been handled'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            loan.loan_status = loan_status
            loan.save()
            
            acc = BankAccount.objects.filter(account_number=account_number).first()
                
            if acc is None:
                return Response({"error": "No account found for this user."}, status=404)
        
            data = {
                "user_id": loan.user_id,
                "amount": loan.amount,
                "duration": loan.duration,
                "currency": "NGN",
                "interest_rate": loan.interest_rate,
                "loan_id": loan.loan_id,
                "status": loan.loan_status,
                "payee_account_id": acc.account_number,
            }

            publish_loan_updated.apply_async(args=[data], queue=
                                             'account_service.internal')
            print('task published')
            return Response({'message': 'Loan updated successfully.'},
                            status=status.HTTP_200_OK)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoanDetailView(APIView):
    serializer_class = LoanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Loan.objects.all()

    def get(self, request, format=None):
        user_id = request.user.id
        loan = Loan.objects.filter(user_id=user_id).first()
        data = {
                'user id': loan.user_id,
                'amount': loan.amount,
                'amount_repayable': loan.amount_to_repay,
                'monthly_repayment': loan.monthly_repayment,
                'interest_rate': loan.interest_rate,
                'duration': loan.duration,
                'loan_status': loan.loan_status,
        }
        return Response(data, status=status.HTTP_200_OK)

class BankPoolDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = BankPool.objects.all()
    
    def get(self, request, format=None):
        bank_pool = BankPool.objects.first()
        data = {
            "total_funds": str(bank_pool.total_funds)
        }
        
        return Response(data, status=status.HTTP_200_OK) 
    
class BankAccountDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = BankAccount.objects.all()
    
    def get(self, request, format=None):
        user_id = request.user.id
        account = BankAccount.objects.filter(user_id=user_id).first()
        ca = {
                'id': account.id,
                'user id': account.user_id,
                'account number': account.account_number,
                'balance': account.balance,
                'interest rate': account.interest_rate,
                'created_at': account.created_at
            }
        return Response(ca, status=status.HTTP_200_OK)
  
  
class CardDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Card.objects.all()
    
    def get(self, request):
        user_id = request.user.id 
        
        card = get_object_or_404(Card, user_id=user_id)
        
        real_card_number = decrypt_data(card.card_number)
        real_card_cvv = decrypt_data(card.cvv)

        data = {
            'user_id': card.user_id,
            'card_number': real_card_number,
            'card_type': card.card_type,
            'cvv': real_card_cvv,
            'active': card.active,
            'expiry_date': card.expiration_date,
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
        
class VerifyCard(APIView):
    serializer_class = CardInputSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = Card.objects.all()
    
    def post(self, request, format=None):
        user_id = request.user.id
        
        # 1. Fetch Card 
        card = get_object_or_404(Card, user_id=user_id)
        
        if not card:
            return Response({'message': 'Card not registered for this user.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 2. Verify Active Status
        if not card.active:
            return Response({'message': 'Card is blocked.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 3. Validate Inputs
        serializer = CardInputSerializer(data=request.data)
        
        if serializer.is_valid():
            input_pin = serializer.validated_data["PIN"]
            input_card_num = serializer.validated_data["card_number"]
            input_cvv = serializer.validated_data["cvv"]
   
            # 3.1 VERIFY PIN
            if not check_password(input_pin, card.PIN):
                return Response({
                    'message': 'Invalid PIN', 
                    'validity': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 3.2 VERIFY CARD NUMBER    
            if input_card_num != decrypt_data(card.card_number):
                return Response({
                    'message': 'Invalid Card Number', 
                    'validity': False
                }, status=status.HTTP_403_FORBIDDEN)
                
            #3.3 VERIFY CARD CVV    
            if input_cvv != decrypt_data(card.cvv):
                return Response({
                    'message': 'Invalid cvv', 
                    'validity': False
                }, status=status.HTTP_403_FORBIDDEN)
                
            data = {"validity": True}   #ALL CHECKS PASSED, CARD IS VALID
            return Response({'message': 'Card Verified.', 'data': data}, status=status.HTTP_200_OK)
        
            """
            # 5. Verify Details Match (Card Number & CVV)
            if input_card_num == card.card_number and input_cvv == card.cvv:
                # Success Payload
                data = {"validity": True}

                return Response({'message': 'Card Verified.', 'data': data}, status=status.HTTP_200_OK)
            
            else:
                # Details Mismatch
                data = {"validity": False}
                
                return Response({
                    'message': 'Card validation failed (CVV or Number mismatch).', 
                    'data': data
                }, status=status.HTTP_403_FORBIDDEN)
            """ 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  
class VerifyAccountPin(APIView):   
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = pinserializer
    
    def post(self, request,format=None):
        
        serializer = pinserializer(data=request.data)
        if serializer.is_valid():
            user_id = request.user.id
            
            input_pin = serializer.validated_data["pin"]
        
            account = BankAccount.objects.filter(user_id=user_id).first()

            if account is None:
                return Response({'message': 'The user has no open bank account'}, 
                                status=status.HTTP_404_NOT_FOUND)          

            if account.active is False:
                return Response ({'message': 'Account is blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            stored_hash = account.PIN
            
            if not check_password(input_pin, stored_hash):
                # The PIN is NOT correct! DO NOT Proceed with the transaction.
                data = {
                "validity": False,
                } 
  
                return Response ({'message': 'Invalid', 'data': data}, status=status.HTTP_403_FORBIDDEN)
            
            data = {
                "validity": True,
            }

            return Response({'message': 'Valid', 'data': data}, status=status.HTTP_200_OK)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class BlockCard(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ] 
    queryset = Card.objects.all()  
    serializer = pinserializer   

    @transaction.atomic
    def post(self, request,  format=None):
        serializer = pinserializer(data=request.data)
        user_id = request.user.id
        if serializer.is_valid():
            input_pin = serializer.validated_data['pin']
            card = Card.objects.filter(user_id=user_id).select_for_update().first()
            
            if not check_password(input_pin, card.PIN):
                return Response({'message': 'Incorrect Pin'}, status=status.HTTP_400_BAD_REQUEST)
            
            card.active = False
            card.save()
            return Response({'message': 'Card blocked successfully.'}, status=status.HTTP_200_OK)        
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlockAccount(APIView):    #REVIEW THIS LOGIC
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,] 
    serializer = pinserializer

    @transaction.atomic
    def post(self, request, format=None):
        serializer = pinserializer(data=request.data)
        
        
        if serializer.is_valid():
            user_id = request.user.id
            input_pin = serializer.validated_data['pin']

            # Lock the row (select_for_update), This pauses other transactions trying to touch this specific row
            account = BankAccount.objects.filter(user_id=user_id).select_for_update().first()

            if account.active is True:
                return Response ({'message': 'Account is already blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            if not check_password(input_pin, account.PIN):
                return Response ({'message': 'Invalid PIN.'}, status=status.HTTP_404_NOT_FOUND)
            
            account.active = False
            account.save()
            return Response({'message': 'Account blocked successfully.'}, status=status.HTTP_200_OK)        
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffBlockAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 
    serializer = blockaccountserializer

    @transaction.atomic
    def post(self, request, format=None):
        serializer = blockaccountserializer(data=request.data)
        
        
        if serializer.is_valid():
            account_number = serializer.validated_data['account_number']
            input_pin = serializer.validated_data['pin']

            # Lock the row (select_for_update), This pauses other transactions trying to touch this specific row
            account = BankAccount.objects.filter(account_number=account_number).select_for_update().first()

            if account.active is False:
                return Response ({'message': 'Account is already blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            if not check_password(input_pin, account.PIN):
                return Response ({'message': 'Invalid PIN.'}, status=status.HTTP_404_NOT_FOUND)
            
            account.active = False
            account.save()
            return Response({'message': 'Account blocked successfully.'}, status=status.HTTP_200_OK)        
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetBalance(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,]   

    def get(self, request, format=None):
        user_id_value = request.user.id
        
        sacc = get_object_or_404(BankAccount, user_id=user_id_value)

        data = {
            'user_id': user_id_value,
            'interest_rate': sacc.interest_rate,
            'balance': sacc.balance,
            'currency': sacc.currency,      
            }
        return Response  ({'message': f'The account details are: {data}'}, status=status.HTTP_200_OK)
        

class CreateTicket(APIView):
    serializer_class = CreateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,]

    def post(self, request, format=None):
        
        serializer = CreateTicketSerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.user.id
            subject = serializer.validated_data['subject']
            complaint = serializer.validated_data['complaint']
            
            IT_Tickets.objects.create(user_id=user_id, subject = subject, complaint=complaint)
            
            return Response({'message': 'Ticket created successfully.'}, status=status.HTTP_201_CREATED)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetAndUpdateTicket(APIView):    #CHECH THISS
    serializer_class = UpdateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = IT_Tickets.objects.all()
    
    def get(self, request, format=None):
        serializer = GetTicketSerializer(data=request.query_params)

        if serializer.is_valid():
            ticket_id = serializer.validated_data['ticket_id']
            ticket = get_object_or_404(IT_Tickets, id =ticket_id)
            
            data = {
                'ticket_id': ticket.id,
                'user_id': ticket.user_id,
                'subject': ticket.subject,
                'complaint': ticket.complaint,
            }
            
            return Response({'message': 'Ticket successfully retrieved.', 'data': data},
                            status=status.HTTP_200_OK) 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, format=None):
        serializer = UpdateTicketSerializer(data=request.data)
        
        if serializer.is_valid():
            id = serializer.validated_data['ticket_id']
            resolved = serializer.validated_data['resolved']
            remarks = serializer.validated_data['remarks']
            ticket = IT_Tickets.objects.filter(id=id).select_for_update().first()
            
            if ticket.resolved == True:
                return Response({'message': 'Ticket has already been resolved'}, 
                                status= status.HTTP_409_CONFLICT)
            
            ticket.resolved = resolved
            ticket.remarks = remarks
            ticket.save()
        
            return Response({'message': 'Ticket updated successfully.'}, status=status.HTTP_200_OK)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetTickets(APIView):
    queryset = IT_Tickets.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        tickets = IT_Tickets.objects.filter(taken=False).all()
        
        for ticket in tickets:
            data = { 
                ticket.complaint
            }
        
        return Response(data, status=status.HTTP_200_OK)
    
class DebitBankPool(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BankSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        acc = BankPool.objects.select_for_update().first()
        acc.total_funds -= amount
        acc.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)
        

class CreditBankPool(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request):
        serializer = BankSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        acc = BankPool.objects.select_for_update().first()
        acc.total_funds += amount
        acc.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)
        

class DebitAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request):
        serializer = DebitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        account_number = serializer.validated_data['account_number']
        amount = serializer.validated_data['amount'] # This is now a Decimal


        # Lock the row (select_for_update), This pauses other transactions trying to touch this specific row
        account = BankAccount.objects.filter(account_number=account_number).select_for_update().first()
            
        if account.active == False:
            return Response({"error": "Account is blocked"}, status=status.HTTP_403_FORBIDDEN)
 
        if account is None:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)


        if account.balance < amount:
            return Response({
                "status": "failed", 
                "message": "Insufficient funds"
            }, status=status.HTTP_400_BAD_REQUEST)

        account.balance -= amount
        account.save()

        return Response({"status": "success", "new_balance": str(account.balance)}, status=status.HTTP_200_OK)
    

class CreditAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):

        serializer = DebitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        account_number = serializer.validated_data['account_number']
        amount = serializer.validated_data['amount'] # This is now a Decimal

        #Lock the row (select_for_update), This pauses other transactions trying to touch this specific row
        account = BankAccount.objects.filter(account_number=account_number).select_for_update().first()
        
        if account.active == False:
                return Response({"error": "Account is blocked"}, status=status.HTTP_403_FORBIDDEN)

        if account is None:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        account.balance += amount
        account.save()

        return Response({"status": "success", "new_balance": str(account.balance)}, status=status.HTTP_200_OK)
