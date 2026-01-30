from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import PaymentRequest

class PaymentTests(APITestCase):
    
    def setUp(self):
        # Create a dummy user for authentication simulation
        # Note: Since we are using JWT/Service Auth, mock the authentication 
        # or force the user into the request if using standard DRF auth.
        class MockUser:
            id = 1
            is_authenticated = True
        self.user = MockUser()

    @patch('payments.views.process_internal_transfer.apply_async')
    @patch('payments.views.transaction.on_commit')
    def test_internal_transfer_success(self, mock_on_commit, mock_celery_task):
        """
        Test that a valid transfer request creates a PENDING record 
        and schedules the Celery task.
        """
        # Mock transaction.on_commit to execute the lambda immediately
        mock_on_commit.side_effect = lambda func: func()

        url = reverse('internal_transfer') # Ensure this matches your urls.py name
        data = {
            "payer_account_id": "1234567890",
            "payee_account_id": "0987654321",
            "amount": "500.00",
            "account_type": "current",
            "currency": "NGN",
            "pin": "1234",
            "payment_type": "INTERNAL"
        }

        # Force authentication (Mocking JWT Auth behavior)
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(url, data, format='json')

        # 1. Assert Response is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'Processing')

        # 2. Assert Database Record Created
        payment = PaymentRequest.objects.get(payer_account_id="1234567890")
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(float(payment.amount), 500.00)

        # 3. Assert Celery Task was called
        mock_celery_task.assert_called_once()
        # Verify arguments passed to task
        args = mock_celery_task.call_args[1]['args'][0]
        self.assertEqual(args['amount'], "500.00")
        self.assertEqual(args['pin'], "1234")

    @patch('payments.views.initiate_card_payment.apply_async')
    @patch('payments.views.transaction.on_commit')
    def test_card_payment_success(self, mock_on_commit, mock_celery_task):
        """
        Test that a card payment request works and triggers the task.
        """
        mock_on_commit.side_effect = lambda func: func()
        
        url = reverse('card_payment') # Ensure matches urls.py
        data = {
            "payee_account_id": "1234567890",
            "amount": "150.00",
            "card_number": "1234567812345678",
            "cvv": "123",
            "pin": "9999",
            "currency": "NGN"
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check DB
        # Note: Card payments might not have payer_account_id initially if it comes from external
        payment = PaymentRequest.objects.get(payee_account_id="0987654321")
        self.assertEqual(payment.status, 'PENDING')

        # Check Celery
        mock_celery_task.assert_called_once()