# apps/course/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Courses
from django.contrib.auth import get_user_model

User = get_user_model()

class PaginationTestCase(APITestCase):
    
    def setUp(self):
        self.user = User(
            email='test@example.com',
            first_name='Test',
            second_name='User', 
            last_name='Testov',
            role_id=1  
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        for i in range(25):
            Courses.objects.create(
                title=f'Test Course {i}',
                description=f'Description {i}',
                section='Math',
                room='101',
                theme='Algebra',
                creator=self.user,
                inv_code=f'inv{i}',
                # course_id_base=f'course{i}',
                config_permission=3,
                delete_permission=0
            )
    
    def test_pagination_settings(self):
        """Тестируем что настройки пагинации применяются"""
        from django.conf import settings
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 20)
        self.assertEqual(settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'], 
                        'rest_framework.pagination.PageNumberPagination')
    
    def test_course_list_pagination(self):
        """Тестируем пагинацию в API"""
        url = reverse('courses-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        self.assertEqual(len(response.data['results']), 20)
        
        self.assertIsNotNone(response.data['next'])
        
        self.assertEqual(response.data['count'], 25)

# python manage.py test apps.course.tests.PaginationTestCase - запуск теста