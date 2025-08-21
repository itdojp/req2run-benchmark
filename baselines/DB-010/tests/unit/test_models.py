"""Unit tests for data models"""
import pytest
from decimal import Decimal
from uuid import uuid4
from pydantic import ValidationError

from src.models import (
    Account,
    TransferRequest,
    TransactionState
)


def test_account_creation():
    """Test account model creation"""
    account = Account(
        id=uuid4(),
        balance=Decimal("100.00"),
        currency="USD",
        version=0
    )
    
    assert account.balance == Decimal("100.00")
    assert account.currency == "USD"
    assert account.version == 0


def test_account_negative_balance_validation():
    """Test that negative balances are rejected"""
    with pytest.raises(ValidationError):
        Account(
            id=uuid4(),
            balance=Decimal("-10.00"),
            currency="USD"
        )


def test_transfer_request_validation():
    """Test transfer request validation"""
    from_id = uuid4()
    to_id = uuid4()
    
    request = TransferRequest(
        from_account_id=from_id,
        to_account_id=to_id,
        amount=Decimal("50.00"),
        idempotency_key="test_key"
    )
    
    assert request.amount == Decimal("50.00")
    assert request.idempotency_key == "test_key"


def test_transfer_request_same_account_validation():
    """Test that transfers to same account are rejected"""
    account_id = uuid4()
    
    with pytest.raises(ValidationError):
        TransferRequest(
            from_account_id=account_id,
            to_account_id=account_id,
            amount=Decimal("50.00"),
            idempotency_key="test_key"
        )


def test_transfer_request_negative_amount_validation():
    """Test that negative amounts are rejected"""
    with pytest.raises(ValidationError):
        TransferRequest(
            from_account_id=uuid4(),
            to_account_id=uuid4(),
            amount=Decimal("-50.00"),
            idempotency_key="test_key"
        )


def test_transfer_request_zero_amount_validation():
    """Test that zero amounts are rejected"""
    with pytest.raises(ValidationError):
        TransferRequest(
            from_account_id=uuid4(),
            to_account_id=uuid4(),
            amount=Decimal("0.00"),
            idempotency_key="test_key"
        )


def test_transaction_states():
    """Test transaction state enum"""
    assert TransactionState.PENDING.value == "pending"
    assert TransactionState.PREPARED.value == "prepared"
    assert TransactionState.COMMITTED.value == "committed"
    assert TransactionState.ROLLED_BACK.value == "rolled_back"
    assert TransactionState.FAILED.value == "failed"