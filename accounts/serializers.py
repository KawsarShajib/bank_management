from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BankAccount

class BankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = BankAccount
        fields = (
            'id', 'account_number', 'account_type', 'balance',
            'owner', 'owner_username', 'status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'account_number', 'balance', 'owner', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

