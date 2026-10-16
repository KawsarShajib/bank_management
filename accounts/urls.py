from django.urls import path
from .views import RegisterView, AccountListCreateView, AccountDetailView

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),

    # Accounts
    path('accounts/', AccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<int:id>/', AccountDetailView.as_view(), name='account-detail'),
]