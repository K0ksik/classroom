# apps/authorization/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from .models import CustomUser
from .permissions import IsVerified

class IsVerifiedPermissionTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsVerified()
        
        # Создаем пользователей
        self.verified_user = CustomUser.objects.create(
            email='verified@test.com', 
            is_verified=True
        )
        self.unverified_user = CustomUser.objects.create(
            email='unverified@test.com', 
            is_verified=False
        )
        self.anonymous_user = None

    def test_verified_user_has_permission(self):
        request = self.factory.get('/')
        request.user = self.verified_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_unverified_user_has_no_permission(self):
        request = self.factory.get('/')
        request.user = self.unverified_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_user_has_no_permission(self):
        request = self.factory.get('/')
        request.user = self.anonymous_user
        self.assertFalse(self.permission.has_permission(request, None))


# python manage.py test apps.authorization - запуск теста