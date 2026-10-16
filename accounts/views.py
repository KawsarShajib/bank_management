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
