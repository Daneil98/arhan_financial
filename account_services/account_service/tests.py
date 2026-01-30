from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import SavingsAccount, Loan, Card

User = get_user_model()

class AccountServiceTests(APITestCase):

    def setUp(self):
        # Setup basic data for tests
        self.user = User.objects.create_user(username='testacc', email='test@acc.com', password='pw')
        self.account = SavingsAccount.objects.create(
            user=self.user, 
            account_number="1000000001", 
            balance=Decimal('1000.00')
        )
        self.client.force_authenticate(user=self.user)

    @patch('account_service.views.encrypt_data') # Mock encryption to verify call
    @patch('account_service.tasks.publish_card_created.apply_async')
    def test_create_card(self, mock_publish, mock_encrypt):
        """
        Test linking a new card to an account.
        """
        # Setup mock return for encryption
        mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

        url = reverse('create_card') 
        data = {
            "account_number": "1000000001",
            "pin": "1234",
            "card_type": "debit"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check DB
        card = Card.objects.get(savings_account=self.account)
        self.assertTrue(card.active)
        # Verify encryption was used (based on our mock side effect)
        self.assertTrue(card.card_number.startswith("encrypted_"))

    def test_loan_approval_money_transaction(self):
        """
        Test that Approving a loan increases the user's account balance.
        This assumes logic is inside the View or Model save method.
        """
        # 1. Create a Pending Loan
        loan = Loan.objects.create(
            user_id=self.user.id,
            account_number=self.account.account_number,
            amount=Decimal('5000.00'),
            duration='12 Months',
            loan_status='pending'
        )

        # 2. Call Approval Endpoint (Simulate Staff Action)
        # Ensure you have a view that handles this, e.g., UpdateLoanStatus
        url = reverse('update_loan') 
        data = {
            "loan_id": str(loan.loan_id),
            "status": "approved"
        }

        # Mock staff permission if needed
        self.user.is_staff = True 
        self.user.save()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Verify Money Transaction
        # Refresh from DB
        self.account.refresh_from_db()
        loan.refresh_from_db()

        # Balance should be 1000 (initial) + 5000 (loan) = 6000
        self.assertEqual(self.account.balance, Decimal('6000.00'))
        self.assertEqual(loan.loan_status, 'approved')
        self.assertIsNotNone(loan.start_date)