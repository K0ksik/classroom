from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Courses, CourseTeachersThrough, CourseStudentsThrough, Themes, Posts, QuestionOptions, CoursePostThrough, Answers, AnswerOptionsThrough, AttachData, Comments

# Inline for Teachers
class CourseTeachersThroughInline(admin.TabularInline):
    model = CourseTeachersThrough
    extra = 1  # Number of empty forms for adding new teachers
    verbose_name = _("Teacher")
    verbose_name_plural = _("Teachers")
    fields = ('teacher', 'status', 'invited_at', 'accepted_at')
    readonly_fields = ('invited_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher')

# Inline for Students
class CourseStudentsThroughInline(admin.TabularInline):
    model = CourseStudentsThrough
    extra = 1  # Number of empty forms for adding new students
    verbose_name = _("Student")
    verbose_name_plural = _("Students")
    fields = ('student', 'status', 'invited_at', 'accepted_at')
    readonly_fields = ('invited_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student')

# Inline for Course Posts
class CoursePostThroughInline(admin.TabularInline):
    model = CoursePostThrough
    extra = 1
    verbose_name = _("Course Post")
    verbose_name_plural = _("Course Posts")
    fields = ('post', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')

@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'section', 'room_number', 'creator', 'config_permission', 'delete_permission', 'is_archive', 'created_at')
    list_filter = ('is_archive', 'config_permission', 'delete_permission', 'created_at')
    search_fields = ('id', 'title', 'section', 'room_number', 'theme', 'inv_code', 'creator__username')
    readonly_fields = ('id', 'created_at', 'inv_code')
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description', 'section', 'room_number', 'theme', 'image')
        }),
        (_('Permissions'), {
            'fields': ('config_permission', 'delete_permission')
        }),
        (_('Metadata'), {
            'fields': ('creator', 'inv_code', 'created_at', 'is_archive')
        }),
    )
    inlines = [CourseTeachersThroughInline, CourseStudentsThroughInline, CoursePostThroughInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator').prefetch_related('teachers', 'students', 'course_connections')

@admin.register(CourseTeachersThrough)
class CourseTeachersThroughAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'status', 'invited_at', 'accepted_at')
    list_filter = ('status', 'invited_at')
    search_fields = ('course__title', 'teacher__username')
    readonly_fields = ('invited_at',)
    fieldsets = (
        (None, {
            'fields': ('course', 'teacher', 'status')
        }),
        (_('Timestamps'), {
            'fields': ('invited_at', 'accepted_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course', 'teacher')

@admin.register(CourseStudentsThrough)
class CourseStudentsThroughAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'status', 'invited_at', 'accepted_at')
    list_filter = ('status', 'invited_at')
    search_fields = ('course__title', 'student__username')
    readonly_fields = ('invited_at',)
    fieldsets = (
        (None, {
            'fields': ('course', 'student', 'status')
        }),
        (_('Timestamps'), {
            'fields': ('invited_at', 'accepted_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course', 'student')

@admin.register(Themes)
class ThemesAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'course__title')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'course')
        }),
        (_('Metadata'), {
            'fields': ('created_at',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')

@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'post_type', 'theme', 'author', 'is_published', 'created_at')
    list_filter = ('post_type', 'is_published', 'created_at')
    search_fields = ('id', 'name', 'description', 'theme__name', 'author__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description', 'post_type', 'theme', 'author')
        }),
        (_('Settings'), {
            'fields': ('is_published', 'max_score', 'deadline', 'question_type', 'can_change', 'can_comment')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme', 'author').prefetch_related('courses')

@admin.register(QuestionOptions)
class QuestionOptionsAdmin(admin.ModelAdmin):
    list_display = ('post', 'title', 'is_right', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__name', 'title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('post', 'title', 'is_right')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')

@admin.register(CoursePostThrough)
class CoursePostThroughAdmin(admin.ModelAdmin):
    list_display = ('post', 'course', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__name', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('post', 'course')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post', 'course')

@admin.register(Answers)
class AnswersAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'score', 'status', 'submitted_at', 'graded_at')
    list_filter = ('status', 'submitted_at', 'graded_at')
    search_fields = ('student__username', 'task__post__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('student', 'task', 'score', 'status', 'attempts')
        }),
        (_('Timestamps'), {
            'fields': ('submitted_at', 'graded_at', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'task__post', 'task__course')

@admin.register(AnswerOptionsThrough)
class AnswerOptionsThroughAdmin(admin.ModelAdmin):
    list_display = ('answer', 'option', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('answer__student__username', 'option__title', 'text')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('answer', 'option', 'text')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('answer', 'option')

@admin.register(AttachData)
class AttachDataAdmin(admin.ModelAdmin):
    list_display = ('link', 'attachment_type', 'subject_type', 'subject_id', 'loader', 'created_at')
    list_filter = ('attachment_type', 'subject_type', 'created_at')
    search_fields = ('link', 'loader__username')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('link', 'attachment_type', 'subject_type', 'subject_id', 'loader')
        }),
        (_('Metadata'), {
            'fields': ('created_at',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('loader')

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'subject_type', 'subject_id', 'created_at')
    list_filter = ('subject_type', 'created_at')
    search_fields = ('content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('content', 'author', 'subject_type', 'subject_id')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')
