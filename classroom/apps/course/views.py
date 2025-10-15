from django.db.models import Q
from rest_framework.decorators import api_view, action
from rest_framework import generics
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import CoursePreviewSerializer, CourseProfileSerializer, CourseMemberSerializer, CourseCommentsSerializer
from .models import Courses, Comments
from django.core.cache import cache



class CourseViewSet(viewsets.ModelViewSet):
    queryset = Courses.objects.select_related("creator")
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'section', 'theme', 'is_archive']

    def get_serializer_class(self):
        if self.action in ['list', 'get_own_courses']:
            return CoursePreviewSerializer
        return CourseProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if self.action == "get_own_courses":
            return queryset.filter(creator_id=user.pk)
        if self.action in ['list', 'retrieve']:
            queryset = queryset.prefetch_related('teachers', 'students')

        if user.is_admin:
            return queryset
        elif user.is_student:
            return queryset.filter(
                student_invites__student=user,
                student_invites__status='accepted'
            )
        elif user.is_teacher:
            print('here')
            return queryset.filter(
                Q(teacher_invites__teacher=user) & Q(teacher_invites__status='accepted') | Q(creator=user),
            )
        return queryset.none()

    @action(detail=False, methods=["get"])
    def get_own_courses(self, request):
        cache_data = cache.get(f'course_{request.user.id}')

        if cache_data:
            return Response(cache_data)
        
        response = {
            "courses": CoursePreviewSerializer(self.get_queryset(), many=True).data
        }

        cache.set(f'course_{request.user.id}', response, 900)
        return Response(response)
        

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.has_user_on_course(request.user):
            raise PermissionDenied()
        
        cache_data = cache.get(f'course_{instance.id}')
        if cache_data:
            return Response(cache_data)

        serializer = self.get_serializer(instance)
        response = serializer.data

        cache.set(f'course_{instance.id}', response, 900)
        return Response(response)

    def perform_destroy(self, instance):
        if not instance.can_user_delete(self.request.user):
            raise PermissionDenied()
        super().perform_destroy(instance)
    

    @action(detail=True, methods=["get"])
    def members(self, request, id = None):
        """Получение участников текущего курса"""
        course = self.get_object()
        students = course.students.all()

        if request.user.is_teacher or request.user.is_admin:
            search = request.GET.get('search', '')
            if search:
                students = students.filter(
                    Q(first_name__icontains=search) | 
                    Q(last_name__icontains=search) |
                    Q(second_name__icontains=search)
                )
        teachers = course.teachers.exclude(role_id = 2)
        return Response({
            "students": CourseMemberSerializer(students, many = True).data,
            "teachers": CourseMemberSerializer(teachers, many = True).data
        })
    
    @action(detail=True, methods=['delete'],  url_path='remove_member/(?P<student_id>[^/.]+)')
    def remove_member(self, request, id=None, student_id=None):
        """Удаление участника из курса"""
        if not request.user.is_teacher and not request.user.is_admin:
            raise PermissionDenied()
        
        course = self.get_object()
        course.students.remove(student_id)
        return Response(status=status.HTTP_200_OK)
    
   
    @action(detail=True, methods=["get", "post"], url_path='posts/(?P<post_id>[^/.]+)/comments')
    def post_comments(self, request, id = None, post_id = None):
        if request.method == 'GET':
            """Получение комментариев для поста"""
            
            comments = Comments.objects.filter(
                subject_id=post_id,
                subject_type='course_post'
            ).select_related('author')
            return Response(CourseCommentsSerializer(comments, many = True).data)
    
        elif request.method == 'POST':
            """Создать комментарий под постом"""
            serializer = CourseCommentsSerializer(data = request.data)
            if serializer.is_valid():
                serializer.save(
                    author=request.user,
                    subject_id=post_id,
                    subject_type='course_post'
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'],  url_path='posts/(?P<post_id>[^/.]+)/comments/remove_comment/(?P<comment_id>[^/.]+)')
    def remove_comment(self, request, id = None, post_id = None, comment_id = None ):
        """Удаление комментария под постом"""
        comment = Comments.objects.get(
                id = comment_id,
                subject_id=post_id,
                subject_type='course_post'
            )
        
        if not comment.can_delete(request.user):
            raise PermissionDenied()
        
        comment.delete()
        return Response(status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['put'],  url_path='posts/(?P<post_id>[^/.]+)/comments/update_comment/(?P<comment_id>[^/.]+)')   
    def update_comment(self, request, id=None, post_id = None, comment_id = None ):
        """Редактировать комментарий"""
        user = request.user
        comment = Comments.objects.get(
                id=comment_id,
                subject_id=post_id,
                subject_type='course_post'
            )
        if not comment.can_edit(request.user):
            raise PermissionDenied()
        
        serializer = CourseCommentsSerializer(comment, data = request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    
    
