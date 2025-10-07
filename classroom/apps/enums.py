from django.db import models
from django.utils.translation import gettext_lazy as _


class Roles(models.IntegerChoices):
    STUDENT = 0, _('Student')
    TEACHER = 1, _('Teacher')
    ADMIN = 2, _('Administrator')


class ConfigPermissions(models.IntegerChoices):
    STUDENTS_ONLY_COMMENTS = 1, _("Students can only comment")
    TEACHERS_ONLY_PUBLISHED = 2, _("Only teachers can publish")
    ALL = 3, _("All permissions")


class DeletePermissions(models.IntegerChoices):
    CREATOR_ONLY = 0, _('Creator only')
    ALL_TEACHERS = 1, _('All teachers')
    NOT_DELETE = 2, _('Not delete')


class InviteStatuses(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    REJECTED = "rejected", _("Rejected")


class PostTypes(models.TextChoices):
    MATERIAL = 'material', _('Material')
    EXERCISE = 'exercise', _('Exercise')
    QUESTION = 'question', _('Question')
    STUDENT_POST = 'student_post', _('Student Post')
    QUIZ = 'quiz', _('Quiz')


class QuestionTypes(models.TextChoices):
    TEXT = 'text', _('Text')
    ONE_CHOICE = 'one_choice', _('One Choice')
    MULTI_CHOICE = 'multi_choice', _('Multi Choice')


class AttachmentTypes(models.TextChoices):
    FILE = 'file', _('File')
    IMAGE = 'image', _('Image')
    VIDEO = 'video', _('Video')
    LINK = 'link', _('Link')


class TaskStatuses(models.TextChoices):
    NOT_STARTED = 'not_started', _('Not Started')
    IN_PROGRESS = 'in_progress', _('In Progress')
    SUBMITTED = 'submitted', _('Submitted')
    GRADED = 'graded', _('Graded')
    RETURNED = 'returned', _('Returned')


class SubjectTypes(models.TextChoices):
    COURSE_POST = 'course_post', _('Course Post')
    STUDENT_ANSWER = 'student_answer', _('Student Answer')
