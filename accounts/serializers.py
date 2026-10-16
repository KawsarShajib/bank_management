from rest_framework import serializers
from .models import BankAccount

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
        read_only_fields = (
            'id', 
            'account_number', 
            'balance', 
            'owner', 
            'created_at', 
            'updated_at'
        )

    def create(self, validated_data):
        # Owner will be set from the logged-in user later
        # For now we can accept owner in the request body (temporary)    
        # validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


