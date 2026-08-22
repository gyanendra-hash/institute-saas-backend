from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Embeds tenant_id and role into the JWT payload so the frontend and
    downstream permission checks don't need an extra API call."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tenant_id"] = user.tenant_id
        token["role"] = user.role
        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "phone", "tenant"]
        read_only_fields = ["id", "tenant"]
