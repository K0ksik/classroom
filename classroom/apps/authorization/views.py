from django.contrib.auth import login, logout, update_session_auth_hash
from django.urls import reverse

from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response

from .serializers import LoginUserSerializer, UserProfileSerializer, \
    ChangePasswordSerializer, RequestPasswordResetSerializer, ResetPasswordSerializer, UserAvatarSerializer
from .models import CustomUser
from .services import send_password_reset_email, send_verification_email


class LoginView(generics.GenericAPIView):
    serializer_class = LoginUserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if not user.is_verified:
            return Response({
                'message': 'Данный аккаунт не верефицирован. Чтобы авторизоваться подтвердите почту',
                'verify_url': reverse("verify-email")
            }, status=status.HTTP_303_SEE_OTHER)

        login(request, user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Успешный вход',
            'requires_verification': not user.is_verified
        }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({
        "message": "Logout successful"
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """Подтверждение email с помощью кода верификации"""
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response(
            {'error': 'Email и код обязательны'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = CustomUser.objects.select_related("verification_code").get(email=email)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    verification_code = user.verification_code
    if not verification_code or verification_code.code != code:
        return Response(
            {'error': 'Неверный код верификации'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if verification_code.is_expired():
        verification_code.delete()
        return Response(
            {'error': 'Срок действия кода истек'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.is_verified = True
    user.save()
    verification_code.delete()

    return Response(
        {'message': 'Email успешно верифицирован'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_verification_code(request):
    email = request.data.get('email')

    if not email:
        return Response(
            {'error': 'Email обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not user.is_verified:
        send_verification_email(user)
        return Response(
            {'message': 'Код верификации отправлен на email'},
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {'message': 'Пользователь уже верифицирован'},
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Смена пароля с проверкой старого пароля"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    update_session_auth_hash(request, user)

    return Response({
        'message': 'Пароль успешно изменен'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def request_password_reset(request):
    """Запрос на сброс пароля - отправка кода на email"""
    serializer = RequestPasswordResetSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = CustomUser.objects.get(email=email)

    send_password_reset_email(user)

    return Response({
        'message': 'Код для сброса пароля отправлен на email'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request):
    """Сброс пароля с помощью кода подтверждения"""
    serializer = ResetPasswordSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    code = serializer.validated_data['code']
    new_password = serializer.validated_data['new_password']

    user = CustomUser.objects.select_related("password_reset_code").get(email=email)
    reset_code = user.password_reset_code

    if not reset_code or reset_code.code != code:
        return Response(
            {'error': 'Неверный код сброса пароля'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if reset_code.is_expired():
        reset_code.delete()
        return Response(
            {'error': 'Срок действия кода истек'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    reset_code.delete()

    return Response({
        'message': 'Пароль успешно изменен'
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])    
def update_avatar(request):
    """Обновление аватара текущего пользователя"""
    user = request.user
    serializer = UserAvatarSerializer(user, data = request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(status=status.HTTP_400_BAD_REQUEST)
