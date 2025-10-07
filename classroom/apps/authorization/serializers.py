from django.contrib.auth import authenticate
from rest_framework.serializers import Serializer, ModelSerializer
from rest_framework.fields import SerializerMethodField, EmailField, CharField, ImageField
from rest_framework.exceptions import ValidationError

from .models import CustomUser

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class UserProfileSerializer(ModelSerializer):

    role_name = SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем список исключаемых полей из context, если он указан
        exclude_fields = self.context.get('exclude_fields', [])
        # Удаляем поля, указанные в exclude_fields, из сериализатора
        for field_name in exclude_fields:
            if field_name in self.fields:
                self.fields.pop(field_name)

    class Meta:
        model = CustomUser
        fields = ("first_name", "second_name", "last_name", "avatar",
                  "role_id", "role_name", "email")

    def get_role_name(self, model_obj):
        return model_obj.role_name

#Отдельный сериализатор для обновления аватарки
class UserAvatarSerializer(ModelSerializer):
    avatar = ImageField(required=True)
    class Meta:
        model = CustomUser
        fields = ("avatar",)


class LoginUserSerializer(Serializer):

    email = EmailField()
    password = CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not (email and password):
            raise ValidationError(
                "Must include 'email' and 'password'"
            )

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )

        if not user or not user.is_active:
            raise ValidationError(
                "Such user does not exists or was delete"
            )
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль неверен")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Пароли не совпадают"})
        
        validate_password(attrs['new_password'])
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=6, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Пароли не совпадают"})
        
        validate_password(attrs['new_password'])
        return attrs

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value