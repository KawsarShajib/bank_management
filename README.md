
# Mini Bank Management System API

A RESTful API built with **Django** and **Django REST Framework (DRF)** that provides core banking operations for customers: registration, authentication, account management, deposits, withdrawals, money transfers, and transaction history. Admin users can view all customers, accounts, and transactions.

---

## Project Description

This project demonstrates:

- REST API design with Django REST Framework
- Token-based authentication
- Proper model relationships (User → BankAccount → Transaction)
- Serializers with validation
- Custom permissions (owner-only + admin)
- Atomic database transactions for money movement
- DecimalField for monetary values
- Pagination and filtering of transaction history
- Clean project structure

**No frontend is included.** 
All endpoints are designed to be tested with Postman, curl, or any HTTP client.

---

## Technology Stack

| Component              | Version                   |
|------------------------|---------------------------|
| Python                 | 3.10+                     |
| Django                 | 5.0+ / 6.x                |
| Django REST Framework  | 3.14+                     |
| Database               | SQLite (default)          |
| Authentication         | DRF Token Authentication  |

---

## Project Structure

```
bank_management/          # Project root
├── manage.py
├── requirements.txt
├── README.md
├── bank_management/      # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/             # Customer auth + Bank accounts
│   ├── models.py         # BankAccount model
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
└── transactions/         # Deposits, withdrawals, transfers
    ├── models.py         # Transaction model
    ├── serializers.py
    ├── views.py
    ├── urls.py
    └── admin.py
```

---

## Installation & Environment Setup

### 1. Prerequisites

- Python 3.10 or higher
- `pip` and `venv` 

### 2. Clone / Create Project Directory

```bash
cd bank_management
```

### 3. Create and Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```
Django>=5.0
djangorestframework>=3.14
```

## Creating the project bank_management

```bash
django-admin startproject bank_management .
```

## Creating the app accounts

```bash
python manage.py startapp accounts
```

### Step 1 —  (only the necessary parts)

```Python
INSTALLED_APPS = [
    # ... default Django apps ...
    # Third party
    'rest_framework',
    # Local apps
    'accounts',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',   # temporary – we will change later
    ],
}
```
We keep permission open for now so we can test account creation easily.

### Step 2 — accounts/models.py

```python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class BankAccount(models.Model):
    ACCOUNT_TYPES = (
        ('SAVINGS', 'Savings'),
        ('CURRENT', 'Current'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CLOSED', 'Closed'),
    )

    account_number = models.CharField(max_length=20, unique=True, editable=False)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account_number} - {self.owner.username}"

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self._generate_account_number()
        super().save(*args, **kwargs)

    def _generate_account_number(self):
        while True:
            number = str(uuid.uuid4().int)[:12]
            if not BankAccount.objects.filter(account_number=number).exists():
                return number
```

```Bash
python manage.py makemigrations accounts
python manage.py migrate
```

### Step 3 — accounts/serializers.py

```Python
from rest_framework import serializers
from .models import BankAccount

class BankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'id',
            'account_number',
            'account_type',
            'balance',
            'owner',
            'owner_username',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'account_number',
            'balance',
            'owner',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        # Owner will be set from the logged-in user later
        # For now we can accept owner in the request body (temporary)
        return super().create(validated_data)
```
