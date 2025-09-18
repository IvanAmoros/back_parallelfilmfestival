from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenObtainPairSerializer
from django.contrib.auth import get_user_model


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs) -> dict[str, str]:
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['is_superuser'] = self.user.is_superuser
        return data


def get(request):
    try:
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
        })
    except Exception as e:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Include the refresh token in the response
        data['refresh'] = attrs['refresh']

        return data

# Password reset
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
