from django.shortcuts import render

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from .models import BankAccount
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    BankAccountSerializer,
    BankAccountDetailSerializer,
    BalanceSerializer,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission: only owner or admin can access."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.owner == request.user


class RegisterView(generics.CreateAPIView):
    """Register a new customer."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Registration successful.'
        }, status=status.HTTP_201_CREATED)


class LoginView(ObtainAuthToken):
    """Customer login - returns auth token."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'message': 'Login successful.'
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """View and update own profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AccountListCreateView(generics.ListCreateAPIView):
    """List own accounts or create a new account."""
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AccountDetailView(generics.RetrieveAPIView):
    """View account details."""
    serializer_class = BankAccountDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(owner=self.request.user)


class AccountBalanceView(generics.RetrieveAPIView):
    """Check account balance."""
    serializer_class = BalanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(owner=self.request.user)


class AdminCustomerListView(generics.ListAPIView):
    """Admin: list all customers."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminAccountListView(generics.ListAPIView):
    """Admin: list all bank accounts."""
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountDetailSerializer
    permission_classes = [permissions.IsAdminUser]
