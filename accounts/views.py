from rest_framework import generics
from .models import BankAccount
from .serializers import BankAccountSerializer


class AccountListCreateView(generics.ListCreateAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class AccountDetailView(generics.RetrieveAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    lookup_field = 'id'
