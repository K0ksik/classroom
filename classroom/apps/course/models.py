from functools import partial

from django.core.files.storage import default_storage
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.core.validators import MinValueValidator, URLValidator
from django.core.exceptions import ValidationError

from apps.utils import generate_random_string, file_upload_path, get_upload_path
from apps.enums import ConfigPermissions, DeletePermissions, InviteStatuses, \
    Roles, PostTypes, QuestionTypes, TaskStatuses, AttachmentTypes, SubjectTypes

from classroom.settings import AUTH_USER_MODEL

from . import fields as _fields


class Courses(models.Model):
    id = _fields.SymbolIdField(_("symbol id"))
    title = models.CharField(_("title"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    section = models.CharField(_("section"), max_length=50, blank=True, null=True)
    room_number = models.CharField(_("room"), max_length=20, blank=True, null=True)
    theme = models.CharField(_("theme"), max_length=25, blank=True, null=True)
    inv_code = models.CharField(_("invite code"), max_length=8, blank=True, null=True)
    config_permission = models.PositiveSmallIntegerField(
        _("config perm"),
        choices=ConfigPermissions,
        default=ConfigPermissions.ALL
    )
    delete_permission = models.PositiveSmallIntegerField(
        _("delete perm"),
        choices=DeletePermissions,
        default=DeletePermissions.CREATOR_ONLY
    )

    creator = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="own_courses",
        verbose_name=_("creator"),
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        _("course image"),
        upload_to=partial(file_upload_path, "course", directory="courses"),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    is_archive = models.BooleanField(_("archive"), default=False)

    teachers = models.ManyToManyField(
        AUTH_USER_MODEL,
        through="CourseTeachersThrough",  # изменено
        verbose_name=_("teachers"),
        related_name="teaching_courses"
    )
    students = models.ManyToManyField(
        AUTH_USER_MODEL,
        through="CourseStudentsThrough",  # изменено
        verbose_name=_("students"),
        related_name="enrolled_courses"
    )

    def has_user_on_course(self, user):
        if user.is_admin or self.creator_id == user.pk:
            return True
        return (
                self.teacher_invites.filter(teacher=user, status='accepted').exists() or
                self.student_invites.filter(student=user, status='accepted').exists()
        )

    def can_user_delete(self, user):
        if user.is_admin:
            return True

        if self.delete_permission == DeletePermissions.CREATOR_ONLY:
            return user.pk == self.creator_id
        elif self.delete_permission == DeletePermissions.ALL_TEACHERS:
            return user.is_teacher and self.teachers.filter(pk=user.pk).exists()
        elif self.delete_permission == DeletePermissions.NOT_DELETE:
            return False

    def can_user_comment(self, user):
        if user.is_admin:
            return True

        if self.config_permission == ConfigPermissions.ALL:
            return True
        elif self.config_permission == ConfigPermissions.STUDENTS_ONLY_COMMENTS:
            return True
        elif self.config_permission == ConfigPermissions.TEACHERS_ONLY_PUBLISHED:
            return user.is_teacher and self.teachers.filter(pk=user.pk).exists()

    def can_user_publish(self, user):
        if user.is_admin:
            return True

        if self.config_permission == ConfigPermissions.ALL:
            return True
        elif self.config_permission == ConfigPermissions.STUDENTS_ONLY_COMMENTS:
            return user.is_teacher and self.teachers.filter(pk=user.pk).exists()
        elif self.config_permission == ConfigPermissions.TEACHERS_ONLY_PUBLISHED:
            return user.is_teacher and self.teachers.filter(pk=user.pk).exists()

    def save(self, *args, **kwargs):
        # Генерируем поля только для новых объектов
        if self.pk is None:
            # Генерируем inv_code только если он не указан
            if not self.inv_code:
                self.inv_code = generate_random_string(
                    self._meta.get_field('inv_code').max_length,
                    use_upper_case=False
                )

        return super().save(*args, **kwargs)


class ActionMixin:

    def accept(self):
        self.accepted_at = timezone.now()
        self.status = InviteStatuses.ACCEPTED
        self.save()

    def reject(self):
        self.status = InviteStatuses.REJECTED
        self.save()


class CourseTeachersThrough(ActionMixin, models.Model):
    teacher = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="teacher_course_invites",
        verbose_name=_("teacher"),
        on_delete=models.CASCADE,
        limit_choices_to={'role_id': Roles.TEACHER}
    )
    course = models.ForeignKey(
        "Courses",
        related_name="teacher_invites",
        verbose_name=_("course"),
        on_delete=models.CASCADE
    )

    invited_at = models.DateTimeField(_("invited_at"), auto_now_add=True)
    accepted_at = models.DateTimeField(_("accepted_at"), default=None)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InviteStatuses.choices,
        default=InviteStatuses.PENDING
    )

    class Meta:
        unique_together = ("teacher", "course")
        verbose_name = _("Course Teacher")
        verbose_name_plural = _("Course Teachers")


class CourseStudentsThrough(ActionMixin, models.Model):
    student = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="course_invites",
        verbose_name=_("student"),
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        "Courses",
        related_name="student_invites",
        verbose_name=_("course"),
        on_delete=models.CASCADE
    )

    invited_at = models.DateTimeField(_("invited at"), auto_now_add=True)
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InviteStatuses.choices,
        default=InviteStatuses.PENDING
    )

    class Meta:
        unique_together = ("student", "course")
        verbose_name = _("Course Student")
        verbose_name_plural = _("Course Students")


class Themes(models.Model):
    name = models.CharField(_("name"), max_length=50)
    course = models.ForeignKey(
        'Courses',
        verbose_name=_("course"),
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        unique_together = ("name", "course_id")
        verbose_name = _("Theme")
        verbose_name_plural = _("Themes")


class Posts(models.Model):
    id = _fields.SymbolIdField(_("symbol id"))
    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    post_type = models.CharField(_("post type"), max_length=20, choices=PostTypes.choices)
    theme = models.ForeignKey(Themes, verbose_name=_("theme"), on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_("author"), on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(_("is published"), default=False)
    max_score = models.IntegerField(_("max score"), null=True, blank=True, validators=[MinValueValidator(0)])
    deadline = models.DateTimeField(_("deadline"), null=True, blank=True)
    question_type = models.CharField(
        _("question type"),
        max_length=20,
        choices=QuestionTypes.choices,
        null=True,
        blank=True
    )
    can_change = models.BooleanField(_("can change"), default=False)
    can_comment = models.BooleanField(_("can comment"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    courses = models.ManyToManyField(
        "Courses",
        through="CoursePostThrough",
        related_name="posts"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_question_type = self.question_type

    @property
    def is_question(self):
        return self.post_type == PostTypes.QUESTION

    @property
    def is_quiz(self):
        return self.post_type == PostTypes.QUIZ

    @property
    def is_student_post(self):
        return self.post_type == PostTypes.STUDENT_POST

    @property
    def is_material(self):
        return self.post_type == PostTypes.MATERIAL

    @property
    def is_exercise(self):
        return self.post_type == PostTypes.EXERCISE

    def clean(self):
        # MATERIAL
        if self.is_material:
            if any([self.max_score is not None, self.deadline is not None,
                    self.question_type is not None, self.can_change, self.can_comment]):
                raise ValidationError({
                    'task_type': 'Material posts cannot have max_score, deadline, '
                                 'question_type, can_change, or can_comment fields set.'
                })

        # EXERCISE
        elif self.is_exercise:
            if self.max_score is None:
                raise ValidationError({
                    'max_score': 'Exercise posts must have max_score set.'
                })
            if self.question_type is not None:
                raise ValidationError({
                    'question_type': 'Exercise posts cannot have question_type set.'
                })

        # QUESTION
        elif self.is_question:
            if self.max_score is None:
                raise ValidationError({
                    'max_score': 'Question posts must have max_score set.'
                })
            if self.question_type is None:
                raise ValidationError({
                    'question_type': 'Question posts must have question_type set.'
                })

        # RESTRUCTION
        if self.author and self.author.is_student:
            errors = {}

            if self.is_student_post:
                errors['task_type'] = 'Students can only create student_post type posts.'

            if self.description is not None:
                errors['description'] = 'Students cannot set description.'

            if self.theme is not None:
                errors['theme'] = 'Students cannot set theme.'

            if self.is_published:
                errors['is_published'] = 'Students cannot publish posts.'

            if self.max_score is not None:
                errors['max_score'] = 'Students cannot set max_score.'

            if self.deadline is not None:
                errors['deadline'] = 'Students cannot set deadline.'

            if self.question_type is not None:
                errors['question_type'] = 'Students cannot set question_type.'

            if self.can_change:
                errors['can_change'] = 'Students cannot set can_change.'

            if self.can_comment:
                errors['can_comment'] = 'Students cannot set can_comment.'

            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        old_question_type = self._current_question_type

        if old_question_type == self.question_type or \
            (old_question_type == QuestionTypes.ONE_CHOICE and
                self.question_type == QuestionTypes.MULTI_CHOICE):

            super().save(*args, **kwargs)
            self._current_question_type = self.question_type
            return

        with transaction.atomic():
            answer_options_through_qs = AnswerOptionsThrough.objects.filter(
                answer__task__post=self
            ).select_related('answer', 'option')
            answer_options_through_qs.delete()
            Answers.objects.select_related('answer', 'option')\
                .filter(task__post=self).update(score=None, status=TaskStatuses.RETURNED)

            # Сохраняем объект Posts после обработки изменений
            super().save(*args, **kwargs)

        # Обновляем _current_question_type после сохранения
        self._current_question_type = self.question_type


class QuestionOptions(models.Model):
    post = models.ForeignKey(
        'Posts',
        verbose_name=_("post"),
        on_delete=models.CASCADE,
        related_name="question_options"
    )
    title = models.TextField(_("title"))
    is_right = models.BooleanField(_("is right"), blank=True, null=True) # если null, то расмматриватькак ответ на опрос
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Question Option")
        verbose_name_plural = _("Question Options")

    def clean(self):
        if self.post is None:
            raise ValidationError(
                "Question options can attach to null post"
            )
        if not (self.post.is_question or self.is_quiz):
            raise ValidationError(
                "Question options can only be added to QUESTION ot QUIZ type of post"
            )
        if self.post.is_question and self.is_right is None:
            raise ValidationError(
                "Question options of QUESTION type of post must have is_right"
            )
        if self.post.is_quiz and self.is_right is not None:
            raise ValidationError(
                "Question options of QUIZ type of post must not have is_right"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CoursePostThrough(models.Model):
    post = models.ForeignKey(
        'Posts',
        verbose_name=_("post"),
        on_delete=models.CASCADE,
        related_name="post_connections"
    )
    course = models.ForeignKey(
        'Courses',
        verbose_name=_("course"),
        on_delete=models.CASCADE,
        related_name="course_connections"
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = _("Course Post Connection")
        verbose_name_plural = _("Course Post Connections")

    def __str__(self):
        return f"{self.course.title} - {self.post.name}"


class Answers(models.Model):
    student = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_("student"),
        on_delete=models.CASCADE,
        limit_choices_to={'role_id': Roles.STUDENT},
        related_name="student_answers"
    )
    task = models.ForeignKey(
        'CoursePostThrough',
        verbose_name=_("task"),
        on_delete=models.CASCADE,
    )

    score = models.IntegerField(
        _("score"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    submitted_at = models.DateTimeField(_("submitted at"), null=True, blank=True)
    graded_at = models.DateTimeField(_("graded at"), null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(_("attempts"), default=0)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=TaskStatuses.choices,
        default=TaskStatuses.NOT_STARTED
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    option_selections = models.ManyToManyField(
        "QuestionOptions",
        through="AnswerOptionsThrough",
        related_name="answer_selections"
    )

    class Meta:
        unique_together = ("student", "task")
        verbose_name = _("Student Answer")
        verbose_name_plural = _("Student Answers")

    def __str__(self):
        return f"Answer by {self.student} for <{self.task}> (Status: {self.status})"

    def save(self, *args, **kwargs):
        post = self.task.post
        if not (post.is_question or post.is_exercise):
            raise ValidationError(f"Student can`t give the answer on {post.post_type}")
        super().save(*args, **kwargs)

    def submit(self):
        """Увеличивает счетчик попыток при сдаче ответа"""
        self.attempts += 1
        self.submitted_at = timezone.now()
        self.status = TaskStatuses.SUBMITTED
        self.save()

    def grade(self, score):
        """Оценивает ответ студента"""
        self.score = score
        self.graded_at = timezone.now()
        self.status = TaskStatuses.GRADED
        self.save()

    def progress(self):
        self.status = TaskStatuses.IN_PROGRESS
        self.save()


class AnswerOptionsThrough(models.Model):
    answer = models.ForeignKey(
        'Answers',
        verbose_name=_("answer"),
        on_delete=models.CASCADE,
    )
    option = models.ForeignKey(
        'QuestionOptions',
        verbose_name=_("option"),
        on_delete=models.CASCADE,
        related_name="selected_by",
        null=True,
        blank=True,
    )
    text = models.TextField(_("answer text"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        unique_together = ("answer", "option")
        verbose_name = _("Student Answer Option")
        verbose_name_plural = _("Student Answer Options")

    def clean(self):
        """Проверка что заполнено только одно поле: либо option, либо answer_text"""
        if not (self.option is None) ^ (self.text is None):
            raise ValidationError(
                "Either option or text must be set, but not both."
            )
        post = self.answer.task.post
        if not post.is_question:
            raise ValidationError(f"Optional answer is only available for question, not {post.post_type}")
        if self.option and post.question_type == QuestionTypes.TEXT:
            raise ValidationError(f"The selective answer is not available for {post.question_type} question type")
        if self.text and post.question_type != QuestionTypes.TEXT:
            raise ValidationError(f"The text answer is not available for {post.question_type} question type")

        if post.question_type in [QuestionTypes.ONE_CHOICE, QuestionTypes.TEXT] and self.pk is None:
            if self.__class__.objects.filter(answer=self.answer).exists():
                raise ValidationError("Can`t give more than one answer when the question suggests one answer")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.option:
            return f"Option {self.option_id} for answer {self.answer_id}"
        else:
            return f"Text answer for answer {self.answer_id}"


class AttachData(models.Model):
    MAX_FILE_SIZE = 2 * (1024 ** 3) # 2 ГБ
    id = _fields.SymbolIdField(_("symbol id"))
    link = models.TextField(_("link"), max_length=250)
    file = models.FileField(_("file"), upload_to=get_upload_path, null=True, blank=True)

    attachment_type = models.CharField(
        _("attachment type"),
        max_length=20,
        choices=AttachmentTypes.choices
    )
    subject_id = models.IntegerField(_("subject id"))
    subject_type = models.CharField(
        _("subject type"),
        max_length=20,
        choices=SubjectTypes.choices
    )
    loader = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_("loader"),
        on_delete=models.CASCADE,
        related_name="load_data"
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def clean(self):
        if self.attachment_type == AttachmentTypes.LINK:
            validator = URLValidator()
            try:
                validator(self.link)
            except ValidationError:
                raise ValidationError({"link": _("Incorrect URL.")})
        elif self.attachment_type == AttachmentTypes.FILE:
            if getattr(self, "_file", None) is None:
                raise ValidationError({"file": _("File not specified.")})

    def upload_file(self, file, save=False):
        if self.attachment_type == AttachmentTypes.FILE:

            if file.size > self.MAX_FILE_SIZE:
                raise ValidationError({"link": _("File size exceeds 10 MB.")})

            file_path = get_upload_path(self, file.name)
            saved_path = default_storage.save(file_path, file)

            self.link = default_storage.url(saved_path)
            if save:
                self.save()
        else:
            raise ValidationError(_("Cannot upload file for link attachment type."))
    def __str__(self):
        return f"{self.get_attachment_type_display()} - {self.link[:50]}"

    def get_subject_object(self):
        """Возвращает объект, к которому прикреплен файл (полиморфная связь)"""
        try:
            if self.subject_type == SubjectTypes.COURSE_POST:
                return CoursePostThrough.objects.get(id=self.subject_id)
            elif self.subject_type == SubjectTypes.STUDENT_ANSWER:
                return Answers.objects.get(id=self.subject_id)
        except (CoursePostThrough.DoesNotExist, Answers.DoesNotExist):
            return None


class Comments(models.Model):
    content = models.TextField(_("content"))
    author = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_("author"),
        on_delete=models.CASCADE,
        related_name='write_comments'
    )
    subject_id = models.IntegerField(_("subject id"))
    subject_type = models.CharField(
        _("subject type"),
        max_length=20,
        choices=SubjectTypes.choices
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        return f"Comment by {self.author} on {self.get_subject_type_display()} #{self.subject_id}"

    def get_subject_object(self):
        """Возвращает объект, к которому относится комментарий (полиморфная связь)"""
        try:
            if self.subject_type == SubjectTypes.COURSE_POST:
                return CoursePostThrough.objects.get(id=self.subject_id)
            elif self.subject_type == SubjectTypes.STUDENT_ANSWER:
                return Answers.objects.get(id=self.subject_id)
        except (CoursePostThrough.DoesNotExist, Answers.DoesNotExist):
            return None

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать комментарий"""
        return user == self.author

    def can_delete(self, user):
        """Проверяет, может ли пользователь удалить комментарий"""
        return user == self.author or user.is_admin
