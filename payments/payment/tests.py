from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PaymentAccount, PaymentRequest


class MockUser:
    """Stand-in for an authenticated identity-service user.

    The payment service has no local auth user table; JWTAuthentication is
    bypassed via force_authenticate, so we only need `id`/`is_authenticated`.
    """
    id = 1
    pk = 1  # DRF's UserRateThrottle keys the cache on request.user.pk
    is_authenticated = True
    is_active = True


class PaymentFlowTests(APITestCase):

    def setUp(self):
        self.user = MockUser()
        # The views derive the payer account number from the caller's
        # PaymentAccount, so it must exist before the request is made.
        self.payer_account = PaymentAccount.objects.create(
            user_id=self.user.id,
            account_number="1234567890",
        )
        self.client.force_authenticate(user=self.user)

    @patch('payment.api.views.process_internal_transfer.apply_async')
    def test_internal_transfer_creates_pending_and_schedules_task(self, mock_task):
        """A valid transfer persists a PENDING record and schedules the worker
        task once the surrounding DB transaction commits."""
        url = reverse('api:internal_transfer')
        data = {
            "payee_account_id": "987654321",
            "amount": "500.00",
            "pin": 1234,
        }

        # on_commit callbacks only fire when the transaction commits; capture
        # and execute them so the scheduling assertion is meaningful.
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Processing')

        payment = PaymentRequest.objects.get(payee_account_id=987654321)
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.amount, Decimal('500.00'))
        self.assertEqual(payment.payer_account_id, 1234567890)

        mock_task.assert_called_once()
        sent = mock_task.call_args.kwargs['args'][0]
        self.assertEqual(sent['amount'], "500.00")
        self.assertEqual(sent['pin'], "1234")
        self.assertEqual(sent['payer_account_id'], "1234567890")

    @patch('payment.api.views.initiate_card_payment.apply_async')
    def test_card_payment_creates_pending_and_schedules_task(self, mock_task):
        """A valid card payment persists a PENDING CARD record and schedules
        the worker task on the dedicated payment queue."""
        url = reverse('api:card_payment')
        data = {
            "payee_account_id": "987654321",
            "amount": "150.00",
            "card_number": "1234567812345678",
            "cvv": 123,
            "pin": 9999,
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Processing')

        payment = PaymentRequest.objects.get(payee_account_id=987654321, payment_type='CARD')
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.amount, Decimal('150.00'))

        mock_task.assert_called_once()
        self.assertEqual(mock_task.call_args.kwargs['queue'], 'payment.internal')
        sent = mock_task.call_args.kwargs['args'][0]
        self.assertEqual(sent['card_number'], "1234567812345678")
        self.assertEqual(sent['cvv'], "123")

    def test_internal_transfer_rejects_invalid_payload(self):
        """Missing required fields should 400 and create no payment record."""
        url = reverse('api:internal_transfer')

        response = self.client.post(url, {"amount": "500.00"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PaymentRequest.objects.count(), 0)
