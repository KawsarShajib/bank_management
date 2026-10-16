
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
    'rest_framework.authtoken', # for Token authentication
    # Local apps
    'accounts',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # TokenAuthentication → clients send Authorization: Token <key>
        'rest_framework.authentication.TokenAuthentication',
        # SessionAuthentication ->Django’s built-in (the default in DRF when you don’t force Token)
        'rest_framework.authentication.SessionAuthentication',
    ],

    # IsAuthenticated → every endpoint requires login by default
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.AllowAny',   # temporary
        'rest_framework.permissions.IsAuthenticated',
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
        # never negative
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ordering & admin display names
        ordering = ['-created_at']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'

    def __str__(self):
        # for a nice display in admin
        return f"{self.account_number} - {self.owner.username} ({self.account_type})"


    def save(self, *args, **kwargs):
        # Override save() → auto-generate unique account number
        if not self.account_number:
            self.account_number = self._generate_account_number()
        super().save(*args, **kwargs)

    def _generate_account_number(self):
        # Helper method for a unique 12-digit account number
        while True:
            number = str(uuid.uuid4().int)[:12]
            if not BankAccount.objects.filter(account_number=number).exists():
                return number

    def can_withdraw(self, amount):
        # Business rule : Check if withdrawal of given amount is possible
        return self.balance >= amount and self.status == 'ACTIVE'
```

```Bash
python manage.py makemigrations accounts
python manage.py migrate
```

### Step 3 — accounts/serializers.py

```Python
from rest_framework import serializers
from .models import BankAccount
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


# Purpose: Convert models <--> JSON and perform validation.
class BankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = BankAccount
        fields = (
            'id', 
            'account_number', 
            'account_type', 
            'balance',
            'owner', 
            'owner_username', 
            'status', 
            'created_at', 
            'updated_at'
        )

        # customers shouldn’t be able to set their own following credentials : 
        read_only_fields = (
            'id', 
            'account_number', 
            'balance', 
            'owner', 
            'status',
            'created_at', 
            'updated_at'
        )

    def create(self, validated_data):
        # Owner will be set from the logged-in user later
        # For now we can accept owner in the request body (temporary)    
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


```

### Step 4 — accounts/views.py

```Python
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import BankAccount
# from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer, BankAccountSerializer


class RegisterView(generics.CreateAPIView):
    """
    Register a new customer.
    Anyone can access this endpoint (no authentication required).
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create authentication token for the new user
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Registration successful.",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_201_CREATED)
    
class AccountListCreateView(generics.ListCreateAPIView):
    """List own accounts or create a new account."""
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:                      # admin sees everything
            return BankAccount.objects.all()
        return BankAccount.objects.filter(owner=user)
    
    def perform_create(self, serializer):
        # owner comes from the token, not from the request body
        serializer.save(owner=self.request.user)

class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(owner=user)

```

### Step 5 — accounts/urls.py

```Python
from django.urls import path
from .views import RegisterView, AccountListCreateView, AccountDetailView

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),

    # Accounts
    path('accounts/', AccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<int:id>/', AccountDetailView.as_view(), name='account-detail'),
]
```

### Step 6 - Connect it in the project - bank_management/urls.py :

```Python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
]
```

### Step 7 Test the Bank Account API with UserRegistrationSerializer and BankAccountSerializer in POSTMAN

Step 1: Create a user first (or you can go with the admin panel)

```postman/body/raw > POST 
http://127.0.0.1:8000/api/auth/register/
```

```JSON
{
  "username": "kawsar",
  "email": "kawsar117@gmail.com",
  "password": "Sonali@123",
  "password2": "Sonali@123"
}
```
We will get a response containing a TOKEN as below. Copy it.

```JSON
{
    "message": "Registration successful.",
    "token": "5d85794118b2938a3c6a8e4320e5ee990c989a67",
    "user": {
        "id": 1,
        "username": "kawsar",
        "email": "kawsar117@gmail.com",
        "first_name": "",
        "last_name": ""
    }
}
```
### Screenshots : 

![alt text](<screenshots/1. use of token while new user registration.png>)

Step 2: Create an account with the generated TOKEN

```POSTMAN > Method : POST --> body -> raw -> json
http://127.0.0.1:8000/api/accounts/
```

```POSTMAN > Headers:
Authorization: Token <paste_your_token_here>
Content-Type : application/json
```

```JSON
{
  "account_type": "SAVINGS"
}
```

account_number  → auto-generated
balance         → starts at 0.00
owner           → automatically set to the logged-in user
status          → defaults to ACTIVE

### Screenshots : 

![alt text](<screenshots/2. successful user registration and token creation.png>)

Step 3: Test in Postman (in this order)

---
#	Request	                            |   Auth header	        |    Expected
--------------------------------------------------------------------------------------------------
1	POST /api/auth/register/	        |   none	            |    201 + token
--------------------------------------------------------------------------------------------------
2	POST /api/auth/login/               |   none	            |    200 + token
    with {"username","password"}	    
--------------------------------------------------------------------------------------------------
3	GET /api/auth/profile/	            |   Token <key>	        |    200
--------------------------------------------------------------------------------------------------
4	PATCH /api/auth/profile/            |   Token <key>	        |    200
    with {"first_name":"Kawsar"}	    
--------------------------------------------------------------------------------------------------
5	POST /api/accounts/                 |   Token <key>	        |    201
    with {"account_type":"SAVINGS"}	
--------------------------------------------------------------------------------------------------
6	GET /api/accounts/	                |   Token <key>	        |    200, only your accounts
--------------------------------------------------------------------------------------------------
7	GET /api/accounts/1/	            |   Token <key>	        |    200
--------------------------------------------------------------------------------------------------
8	GET /api/accounts/1/balance/	    |   Token <key>	        |    200
--------------------------------------------------------------------------------------------------
9	GET /api/admin/customers/	        |   customer token	    |    403
--------------------------------------------------------------------------------------------------
10	Log in as the superuser, then       |   admin token	        |    200
    GET /api/admin/customers/ and 
    GET /api/admin/accounts/	
---
```

### Screenshots : 

![alt text](<screenshots/3. new account creation via POSTMAN.png>)

![alt text](<screenshots/4. get created account number.png>)

![alt text](<screenshots/5. get all created account numbers of the logged in user.png>)

![alt text](<screenshots/6. Admin Panel.png>)




