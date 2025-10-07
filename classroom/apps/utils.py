import os
import secrets
import string

from django.core.exceptions import ValidationError

from .enums import SubjectTypes


def generate_random_string(length, use_upper_case=True, use_digits=True):
    characters = ''
    if use_upper_case:
        characters += string.ascii_letters
    else:
        characters += string.ascii_lowercase
    if use_digits:
        characters += string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def file_upload_path(prefix, instance, filename, directory=None):
    ext = filename.split('.')[-1]
    filename = f"{prefix}_{generate_random_string(10)}.{ext}"
    return os.path.join(directory or prefix, filename)


def attach_data_path(prefix, instance, filename, directory=None):
    ext = filename.split('.')[-1]
    filename = f"{prefix}_{filename}.{ext}"
    return os.path.join(directory or prefix, filename)


def get_upload_path(instance, filename):
    """Генерирует путь для сохранения файла на основе subject_type и связанных объектов."""
    original_name, ext = os.path.splitext(filename)
    unique_filename = f"{original_name}_%suf_{generate_random_string(6, use_upper_case=False)}{ext}"

    subject = instance.get_subject_object()
    if subject is None:
        raise ValidationError("Invalid subject type.")

    if instance.subject_type == SubjectTypes.COURSE_POST:
        course_id = subject.course.id
        return f'attachments/{course_id}/{instance.subject_id}/post/{unique_filename}'

    elif instance.subject_type == SubjectTypes.STUDENT_ANSWER:
        course_id = subject.task.course.id
        student_id = subject.student.id
        return f'attachments/{course_id}/{subject.task.id}/answers/{student_id}/{unique_filename}'