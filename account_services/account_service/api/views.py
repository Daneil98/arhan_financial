from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from ..models import *
from ..tasks import *
from rest_framework import status
from .serializers import *
from ..generator import *
from ..permissions import *

class DashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Account.objects.all()

    def get(self, request, format=None):
        user_id_value = request.user.id

        savings_account = SavingsAccount.objects.filter(user_id=user_id_value).first()
        current_account = CurrentAccount.objects.filter(user_id=user_id_value).first()
        card = Card.objects.filter(user_id=user_id_value).first()
        loan = Loan.objects.filter(user_id=user_id_value).first()

        data = {
            'savings_account': SavingsAccountSerializer(savings_account).data if savings_account else None,
            'current_account': CurrentAccountSerializer(current_account).data if current_account else None,
            'card': CardSerializer(card).data if card else None,
            'loan': LoanSerializer(loan).data if loan else None,
        }
        return Response(data, status=status.HTTP_200_OK)
       


class CreateSavingsAccount(APIView):
    serializer_class = SavingsAccountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = SavingsAccount.objects.all()
    
    @transaction.atomic
    def post(self, request, format=None):
        
        serializer = SavingsAccountSerializer(data=request.data)   
        if serializer.is_valid():
                      
            user_id_value = request.user.id
            
            print(user_id_value)
            #user_id = serializer.validated_data["user_id"]
            
            if SavingsAccount.objects.filter(user_id=user_id_value).exists():
                return Response({'message': 'You already have a savings account'}, 
                                status= status.HTTP_409_CONFLICT)
        
            hashed_pin_value = make_password(serializer.validated_data["PIN"])
            serializer.save(user_id = user_id_value, PIN=hashed_pin_value, account_number = generate_account_number())
            acc_data = get_object_or_404(SavingsAccount, user_id=user_id_value)
            
            data = {
                "user_id": acc_data.user_id,
                "account_number": acc_data.account_number,
                "balance": acc_data.balance,
                "interest_rate": acc_data.interest_rate,
                "PIN": acc_data.PIN,    
                "currency": acc_data.currency,
                "active": acc_data.active, # Assuming this field is appropriate for current account status
                "created_at": acc_data.created_at.isoformat(),
            }
            publish_savingsAccount_created.apply_async(args=[data], countdown=10)
        
            return Response({'message': 'Savings account created successfully.'}, status=status.HTTP_201_CREATED)  
            
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateCurrentAccount(APIView):
    serializer_class = CurrentAccountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = CurrentAccount.objects.all()
    
    @transaction.atomic
    def post(self, request, format=None):
        
        user_id = request.user.id
        serializer = CurrentAccountSerializer(data=request.data)
        if serializer.is_valid():
            if CurrentAccount.objects.filter(user_id = user_id).exists():
                return Response({'message': 'You already have a current account'}, 
                                status= status.HTTP_409_CONFLICT)
        
            hashed_pin_value = make_password(serializer.validated_data["PIN"])
            
            serializer.save(user_id=user_id, PIN=hashed_pin_value, account_number = generate_account_number())
            acc_data = get_object_or_404(CurrentAccount, user_id=user_id)
             
            data = {
                "user_id": acc_data.user_id,
                "account_number": acc_data.account_number,
                "balance": acc_data.balance,
                #"PIN": acc_data.PIN,
                "interest_rate": acc_data.interest_rate,
                "currency": acc_data.currency,
                "active": acc_data.active, # Assuming this field is appropriate for current account status
                "created_at": acc_data.created_at.isoformat(),
            }
            publish_currentAccount_created.apply_async(args=[data], countdown=10)
            return Response({'message': 'current account created successfully.'}, status=status.HTTP_201_CREATED)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateLoanApplication(APIView):
    serializer_class = LoanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()

    @transaction.atomic
    def post(self, request, format=None):
        serializer = LoanSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = request.user.id
        
            if Loan.objects.filter(user_id=user_id, loan_status__in=["Pending", "approved"]).exists():
                return Response({'message': 'You already have an existing loan or loan application'}, 
                                status= status.HTTP_409_CONFLICT)
            else:
                serializer.save(user_id =user_id, loan_status='pending', start_date=datetime.now())
                
                                       
                loan_data = get_object_or_404(Loan, user_id=user_id)

                data = {
                    "loan_id": loan_data.loan_id,
                    "user_id": loan_data.user_id,
                    "amount": loan_data.amount,
                    "currency": loan_data.currency,
                    "duration": loan_data.duration,
                    "loan_status": loan_data.loan_status,
                    "start_date": loan_data.start_date.isoformat(),
                                        
                }
                publish_loan_applied.apply_async(args=[data], countdown=10)
                return Response({'message': 'Loan application submitted successfully.'},
                            status=status.HTTP_201_CREATED)    
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetAndUpdateLoan(APIView):    #CHECH THISS
    serializer_class = UpdateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.all()
    
    def get(self, request):
        serializer = GetLoanSerializer(data = request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            loan = get_object_or_404(Loan, user_id=user_id)
            
            loan_data = {
                'user_id': loan.user_id,
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
        
    def post(self, request, format=None):
        serializer = UpdateLoanSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            loan_status = serializer.validated_data['status']
            
            loan = get_object_or_404(Loan, user_id=user_id)
            
            if loan.loan_status in ['Rejected', 'Approved']:
                return Response({'message': 'Loan has been handled'}, status=status.HTTP_200_OK)
            
            loan.loan_status = loan_status
            loan.save()
            
            acc = SavingsAccount.objects.filter(user_id=user_id).first()
            account_type = 'savings'
            
            if acc is None:
                acc = CurrentAccount.objects.filter(user_id=user_id).first()
                account_type = 'current'
                
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
                "account_type": account_type,
            }
            
            print("About to publish task")
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
        loan = get_object_or_404(Loan, user_id=user_id)
        data = {
                'user id': loan.user_id,
                'amount': loan.amount,
                'interest rate': loan.interest_rate,
                'duration': loan.duration,
                'loan status': loan.loan_status,
        }
        return Response(data, status=status.HTTP_200_OK)
    
    
class CurrentAccountDetails(APIView):
    serializer_class = CurrentAccountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CurrentAccount.objects.all()
    
    def get(self, request, format=None):
        user_id = request.user.id
        account = get_object_or_404(CurrentAccount, user_id=user_id)
        ca = {
                'id': account.id,
                'user id': account.user_id,
                'account number': account.account_number,
                'balance': account.balance,
                'interest rate': account.interest_rate,
                'created_at': account.created_at
            }
        return Response(ca, status=status.HTTP_200_OK)
  
  
class SavingsAccountDetails(APIView):
    serializer_class = SavingsAccountSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = SavingsAccount.objects.all()
    
    def get(self, request, format=None):
        user = request.user
        user_id = user.id
        account = get_object_or_404(SavingsAccount, user_id=user_id)
        account = {
                'id': account.id,
                'user id': account.user_id,
                'account number': account.account_number,
                'balance': account.balance,
                'interest rate': account.interest_rate,
                'created_at': account.created_at
            }
        return Response(account, status=status.HTTP_200_OK)
  
        
class CreateCard(APIView):
    serializer_class = CardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = Card.objects.all()
    
    @transaction.atomic
    def post(self, request, format=None):
        user_id = request.user.id
        serializer = CardSerializer(data=request.data)
        
        if serializer.is_valid():
            account_type = serializer.validated_data["account_type"]
            acc_type_lower = account_type.lower()
            if Card.objects.filter(user_id=user_id).exists():
                return Response({'message': 'You already have a card'}, 
                                status= status.HTTP_409_CONFLICT)
            
            else:
                hashed_pin_value = make_password(serializer.validated_data["pin"])
                if acc_type_lower == 'savings':
                    acc = get_object_or_404(SavingsAccount, user_id=user_id)
                    Card.objects.create(
                        user_id = user_id,
                        card_number = generate_card_number(),
                        cvv = generate_cvv(),
                        PIN = hashed_pin_value,
                        current_account = acc,)
                else:
                    acc = get_object_or_404(CurrentAccount, user_id=user_id)
                    Card.objects.create(
                        user_id = user_id,
                        card_number = generate_card_number(),
                        cvv = generate_cvv(),
                        PIN = hashed_pin_value,
                        current_account = acc,)
                card_details = get_object_or_404(Card, user_id=user_id)
                data = {
                    #'id': card_details.id,
                    'user_id': card_details.user_id,
                    'card_number': card_details.card_number,
                    'card_type': card_details.card_type,
                    #'PIN': card_details.PIN,
                    #'expiration_date': card_details.expiration_date,
                    #'cvv': card_details.cvv,
                    'active': card_details.active,
                    #'issued_date': card_details.issued_date.isoformat(),
                }
                publish_card_created.apply_async(args=[data], countdown=10)
                return Response ({'message': 'Card created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response ({'message': 'Error creating card.'}, status=status.HTTP_400_BAD_REQUEST)
        
        
class VerifyCard(APIView):
    serializer_class = CardInputSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = Card.objects.all()
    
    @transaction.atomic
    def post(self, request, format=None):
        user_id = request.user.id
        
        # 1. Fetch Card (Correct Way)
        # Use filter().first() instead of get_object_or_404 so we can control the error message
        card = Card.objects.filter(user_id=user_id).first()
        
        if not card:
             return Response({'message': 'Card not registered for this user.'}, status=status.HTTP_404_NOT_FOUND)

        # 2. Validate Inputs
        # Use the specific serializer that doesn't check uniqueness
        serializer = CardInputSerializer(data=request.data)
        
        if serializer.is_valid():
            input_pin = serializer.validated_data["PIN"]
            input_card_num = serializer.validated_data["card_number"]
            input_cvv = serializer.validated_data["cvv"]

            # 3. VERIFY PIN
            if not check_password(input_pin, card.PIN):
                # FIXED: Don't return 'data' here because it doesn't exist yet!
                return Response({
                    'message': 'Invalid PIN', 
                    'validity': False
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 4. Verify Active Status
            if not card.active:
                return Response({'message': 'Card is blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            # 5. Verify Details Match (Card Number & CVV)
            if input_card_num == card.card_number and input_cvv == card.cvv:
                
                # Determine Account Type
                if card.savings_account:
                    # Accessing related object directly is safer/cleaner
                    acc_type = 'savings'
                elif card.current_account:
                    acc_type = 'current'
                else:
                    return Response({'message': 'Card has no linked account.'}, status=400)

                # Success Payload
                data = {
                    "validity": True,
                    "account_type": acc_type
                }
                
                # Publish Event
                publish_verify_card.apply_async(args=[data], countdown=2)
                
                # FIXED: Use 200 OK for success, not 302 Found (which is a redirect)
                return Response({'message': 'Card Verified.', 'data': data}, status=status.HTTP_200_OK)
            
            else:
                # Details Mismatch
                data = {"validity": False}
                # Publish failure event if needed
                # publish_verify_card.apply_async(args=[data], countdown=2)
                
                return Response({
                    'message': 'Card validation failed (CVV or Number mismatch).', 
                    'data': data
                }, status=status.HTTP_403_FORBIDDEN)
                
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class VerifyCardPin(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    queryset = Card.objects.all()
    
    def post(self, request, format=None):
        serializer = CardSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = request.user.id
            acc = get_object_or_404(Card, user_id=user_id)
            
            # 1. Retrieve the stored account object
            stored_hash = acc.PIN

            # The PIN entered by the user (e.g., from a request)
            input_pin = serializer.validated_data["PIN"]

            # 2. VERIFY the PIN
            if not check_password(input_pin, stored_hash):
                # The PIN is NOT correct! DO NOT Proceed with the transaction.
                data = {
                "validity": False,
                }  
                publish_verify_pin.apply_async(args=[data], countdown=10)    
                return Response ({'message': 'Invalid', 'data': data}, status=status.HTTP_403_FORBIDDEN)
            
            # The PIN is CORRECT! Proceed with the transaction.
            data = {
                "validity": True,
            }
            publish_verify_pin.apply_async(args=[data], countdown=10)
            return Response({'message': 'Valid', 'data': data}, status=status.HTTP_200_OK)
              
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class VerifyAccountPin(APIView):   #CHECK THIS LOGIC
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    serializer_class = accountserializers
    
    def post(self, request,format=None):
        
        serializer = accountserializers(data=request.data)
        if serializer.is_valid():
            user_id = request.user.id
            
            input_pin = serializer.validated_data["pin"]
            account_type = serializer.validated_data["account_type"]
            
            acc_type_lower = account_type.lower()
            if acc_type_lower == 'savings':
                acc = get_object_or_404(SavingsAccount, user_id=user_id)
                
            elif acc_type_lower == 'current':
                acc = get_object_or_404(CurrentAccount, user_id=user_id)
             
            else:
                return Response ({'message': 'The user has no open bank account'}, 
                                 status=status.HTTP_404_NOT_FOUND)
            
            if not acc.active:
                return Response ({'message': 'Account is blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            stored_hash = acc.PIN
            
            if not check_password(input_pin, stored_hash):
                # The PIN is NOT correct! DO NOT Proceed with the transaction.
                data = {
                "validity": False,
                } 
                publish_verify_pin.apply_async(args=[data], countdown=10)    
                return Response ({'message': 'Invalid', 'data': data}, status=status.HTTP_403_FORBIDDEN)
            
            data = {
                "validity": True,
            }
            publish_verify_pin.apply_async(args=[data], countdown=10)
            return Response({'message': 'Valid', 'data': data}, status=status.HTTP_200_OK)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class BlockCard(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ] 
    queryset = Card.objects.all()  
    serializer = CardSerializer   

    @transaction.atomic
    def post(self, request,  format=None):
        serializer = CardSerializer(data=request.data)
        user_id = request.user.id
        if serializer.is_valid():
            input_pin = serializer.validated_data['PIN']
            card = get_object_or_404(Card, user_id=user_id)
            
            if not check_password(input_pin, card.PIN):
                return Response({'message': 'Incorrect Pin'}, status=status.HTTP_400_BAD_REQUEST)
            
            card.active = False
            card.save()
            publish_block_card.apply_async(args=[card.active], countdown=10)
            return Response({'message': 'Card blocked successfully.'}, status=status.HTTP_200_OK)        
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlockAccount(APIView):    #REVIEW THIS LOGIC
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,] 
    serializer = accountserializer 

    @transaction.atomic
    def post(self, request, format=None):
        serializer = accountserializer(data=request.data)
        
        if serializer.is_valid():
            
            user_id = request.user.id
            account_type = serializer.validated_data['account_type']
            input_pin = serializer.validated_data['pin']
            
            acc_type_lower = account_type.lower()
            if acc_type_lower == 'savings':
                acc = get_object_or_404(SavingsAccount, user_id=user_id)
                
            elif acc_type_lower == 'current':
                acc = get_object_or_404(CurrentAccount, user_id=user_id)
            
            if not acc.active:
                return Response ({'message': 'Account is already blocked.'}, status=status.HTTP_403_FORBIDDEN)
            
            
            if not check_password(input_pin, acc.PIN):
                return Response ({'message': 'Invalid PIN.'}, status=status.HTTP_404_NOT_FOUND)
            
            acc.active = False
            acc.save()
            publish_block_account.apply_async(args=acc.active, countdown=10)
            return Response({'message': 'Account blocked successfully.'}, status=status.HTTP_200_OK)        
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetBalance(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,]   

    def post(self, request, format=None):
        serializer = accountserializer(data=request.data)
        
        if serializer.is_valid():
            user_id_value = request.user.id
            
            account_type = serializer.validated_data['account_type']
            acc_type_lower = account_type.lower()
            
            if acc_type_lower == 'Savings':
                acc = get_object_or_404(SavingsAccount, user_id=user_id_value)
                
            elif acc_type_lower == 'current':
                acc = get_object_or_404(CurrentAccount, user_id=user_id_value)
            
            else:
                return Response ({'message': 'The user has no open bank account'}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'user_id': acc.user_id,
                'interest_rate': acc.interest_rate,
                'balance': acc.balance,
                'currency': acc.currency       
                }
            publish_get_balance.apply_async(args=[data], countdown=10)
            return Response  ({'message': f'The account details are: {data}'}, status=status.HTTP_200_OK)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
       
        

class CreateTicket(APIView):
    serializer_class = CreateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,]

    def post(self, request, format=None):
        
        serializer = CreateTicketSerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.user.id
            complaint = serializer.validated_data['complaint']
            
            data = IT_Tickets.objects.create(user_id=user_id, complaint=complaint)
            
            info = {
                "id": data.id,
                "user_id": data.user_id,
                "complaint": data.complaint,
                "created_at": data.created_at.isoformat()
            }
            
            publish_ticket_created.apply_async(args=[info], countdown=10)
            return Response({'message': 'Ticket created successfully.'}, status=status.HTTP_201_CREATED)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetAndUpdateTicket(APIView):    #CHECH THISS
    serializer_class = UpdateTicketSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsIT, ]
    queryset = IT_Tickets.objects.all()
    
    def get(self, request, format=None):
        serializer = UpdateTicketSerializer(data = request.data)

        if serializer.is_valid():
            ticket = get_object_or_404(IT_Tickets, ticket_id = serializer.ticket_id)
            
            return Response({'message': 'Ticket successfully retrieved.', 'ticket_data': {ticket}},
                            status=status.HTTP_200_OK) 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, format=None):
        serializer = UpdateTicketSerializer(data=request.data)
        
        if serializer.is_valid():
            ticket = get_object_or_404(IT_Tickets, id=serializer.ticket_id, user_id=id)
            
            if ticket.taken:
                return Response({'message': 'Ticket is already taken'}, 
                                status= status.HTTP_409_CONFLICT)
            
            ticket.taken = True
            ticket.save()
            
            publish_ticket_updated.apply_async(args=[ticket], countdown=10)
            return Response({'message': 'Ticket updated successfully.'}, status=status.HTTP_200_OK)  
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetTickets(APIView):
    queryset = IT_Tickets.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsIT, ]
    
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
        acc = BankPool.objects.first()
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
        acc = BankPool.objects.first()
        acc.total_funds += amount
        acc.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)
        

class DebitAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request):
        # 1. Validate Data
        serializer = DebitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Extract Validated Data
        account_number = serializer.validated_data['account_number']
        amount = serializer.validated_data['amount'] # This is now a Decimal
        account_type = serializer.validated_data['account_type']

        try:
            with transaction.atomic():
                # 3. Select Model based on type
                model = SavingsAccount if account_type == 'savings' else CurrentAccount
                
                # 4. Lock the row (select_for_update)
                # This pauses other transactions trying to touch this specific row
                try:
                    account = model.objects.select_for_update().get(account_number=account_number)
                except model.DoesNotExist:
                    return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

                # 5. Check Balance
                if account.balance < amount:
                    return Response({
                        "status": "failed", 
                        "message": "Insufficient funds"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # 6. Deduct and Save
                account.balance -= amount
                account.save()

                return Response({
                    "status": "success", 
                    "new_balance": str(account.balance)
                }, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch unexpected DB errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditAccount(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 1. Validate Data
        serializer = DebitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Extract Validated Data
        account_number = serializer.validated_data['account_number']
        amount = serializer.validated_data['amount'] # This is now a Decimal
        account_type = serializer.validated_data['account_type']

        try:
            with transaction.atomic():
                # 3. Select Model based on type
                model = SavingsAccount if account_type == 'savings' else CurrentAccount
                
                # 4. Lock the row (select_for_update)
                # This pauses other transactions trying to touch this specific row
                try:
                    account = model.objects.select_for_update().get(account_number=account_number)
                except model.DoesNotExist:
                    return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

                # 5. Add and Save
                account.balance += amount
                account.save()

                return Response({
                    "status": "success", 
                    "new_balance": str(account.balance)
                }, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch unexpected DB errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)