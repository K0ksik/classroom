from django.db import transaction
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import Courses, CourseTeachersThrough
from ..authorization.serializers import UserProfileSerializer
from ..authorization.models import CustomUser


class CreatorSerializerMixin:

    def get_creator(self, model_obj):
        creator = model_obj.creator
        avatar_url = None
        if hasattr(creator, 'avatar') and creator.avatar and creator.avatar.name:
            try:
                print(creator)
                avatar_url = creator.avatar.url
            except ValueError:
                avatar_url = None  # Если файла нет, возвращаем None
        return {
            "first_name": creator.first_name,
            "second_name": creator.second_name,
            "last_name": creator.last_name,
            "avatar": avatar_url
        }

class CoursePreviewSerializer(CreatorSerializerMixin, ModelSerializer):
    creator = SerializerMethodField()

    class Meta:
        model = Courses
        exclude = ("inv_code", "is_archive", "created_at", "teachers", "students",
                   "config_permission", "delete_permission")


class CourseProfileSerializer(CreatorSerializerMixin, ModelSerializer):
    creator = SerializerMethodField()
    # course_id_base = ReadOnlyField()
    user_perms = SerializerMethodField(read_only=True)
    students = UserProfileSerializer(many=True, read_only=True, context={'exclude_fields': ['email']})
    teachers = UserProfileSerializer(many=True, read_only=True, context={'exclude_fields': ['email']})

    class Meta:
        model = Courses
        exclude = ("inv_code", "created_at",)

    def get_user_perms(self, model_obj):
        request = self.context["request"]
        user = request.user

        return {
            "is_creator": user.pk == model_obj.creator_id,
            "is_teacher": user.is_teacher,
            "is_admin": user.is_admin,
            "can_user_delete": model_obj.can_user_delete(user),
            "can_user_comment": model_obj.can_user_comment(user),
            "can_user_publish": model_obj.can_user_publish(user)
        }

    def create(self, validated_data):
        creator = self.context["request"].user
        if creator.is_student:
            raise PermissionDenied()

        validated_data["creator"] = creator
        with transaction.atomic():
            course = super().create(validated_data)

            invite = CourseTeachersThrough(teacher=creator, course=course)
            invite.accept()
            return course

    def update(self, instance, validated_data):
        if instance.creator_id != self.context["request"].user.pk:
            raise PermissionDenied()
        return super().update(instance, validated_data)
    
#Сериализатор для отображения участников курса
class CourseMemberSerializer(ModelSerializer):
    full_name = SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ("id", "full_name", "avatar")

    def get_full_name(self, model_obj):
        fullname = [model_obj.second_name, model_obj.first_name, model_obj.last_name]
        return " ".join(part for part in fullname if part)

