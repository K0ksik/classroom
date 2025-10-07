from django.core.mail import send_mail
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from django.utils import timezone

from datetime import timedelta
from functools import partial

from .managers import CustomUserManager

from apps.utils import file_upload_path
from apps.enums import Roles

from classroom.settings import AUTH_USER_MODEL


class CustomUser(AbstractBaseUser, PermissionsMixin):

    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    second_name = models.CharField(_("second name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)

    avatar = models.ImageField(
        _("avatar"),
        upload_to=partial(file_upload_path, "user", directory="avatars"),
        blank=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png'])
        ]
    )

    role_id = models.PositiveSmallIntegerField(_("role"), choices=Roles, default=Roles.STUDENT)
    email = models.EmailField(_("email address"), unique=True, blank=True)

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    
    is_verified = models.BooleanField(_("verify"), default=False)
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    objects = CustomUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta(AbstractUser.Meta):
        verbose_name = _("user")
        verbose_name_plural = _("users")
        swappable = "AUTH_USER_MODEL"

    @property
    def role_name(self):
        return Roles(self.role_id).name

    @property
    def is_student(self):
        return self.role_id == Roles.STUDENT

    @property
    def is_teacher(self):
        return self.role_id == Roles.TEACHER

    @property
    def is_admin(self):
        return self.role_id == Roles.ADMIN

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def get_fullname(self):
        return f"{self.second_name} {self.first_name} {self.last_name if self.last_name else ''}"

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class ExpiredCodesAbstractModel(models.Model):
    EXPIRE_MINUTES = 5

    user = models.OneToOneField(
        AUTH_USER_MODEL,
        related_name="code",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )
    code = models.CharField(_("code"), max_length=6)
    sent_at = models.DateTimeField(_("sent at"), auto_now_add=True)
    expire_at = models.DateTimeField(_("expire at"))


    def is_expired(self):
        """Проверяет истек ли срок действия кода"""
        return timezone.now() > self.expire_at

    def save(self, *args, **kwargs):
        if not self.expire_at:
            self.expire_at = timezone.now() + timedelta(minutes=self.EXPIRE_MINUTES)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True

class VerifiedCodesModel(ExpiredCodesAbstractModel):

    user = models.OneToOneField(
        AUTH_USER_MODEL,
        related_name="verification_code",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )
    code = models.CharField(_("verification code"), max_length=6)

    class Meta:
        verbose_name = _("Verification Code")
        verbose_name_plural = _("Verification Codes")

    def __str__(self):
        return f"Verification code for {self.user.email}"


class PasswordResetCodesModel(ExpiredCodesAbstractModel):

    user = models.OneToOneField(
        AUTH_USER_MODEL,
        related_name="password_reset_code",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )
    code = models.CharField(_("reset code"), max_length=6)

    class Meta:
        verbose_name = _("Password Reset Code")
        verbose_name_plural = _("Password Reset Codes")

    def __str__(self):
        return f"Reset code for {self.user.email}"