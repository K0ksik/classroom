from django.db import models
from django.utils.translation import gettext_lazy as _

from classroom.settings import AUTH_USER_MODEL


class Notifications(models.Model):
    title = models.CharField(_("title"), max_length=100)
    description = models.TextField(_("description"))
    metadata = models.JSONField(_("metadata"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    recipients = models.ManyToManyField(
        AUTH_USER_MODEL,
        through="NotificationsUsersThrough",
        verbose_name=_("recipients"),
        related_name="received_notifications"
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.date()})"

    @classmethod
    def create_notification(cls, title, description, metadata=None, recipients=None):
        """Создает уведомление и рассылает его получателям"""
        notification = cls.objects.create(
            title=title,
            description=description,
            metadata=metadata or {}
        )

        if recipients:
            through_objects = [
                NotificationsUsersThrough(notification=notification, recipient=recipient)
                for recipient in recipients
            ]
            NotificationsUsersThrough.objects.bulk_create(through_objects)

        return notification

    def get_recipients_count(self):
        """Возвращает количество получателей уведомления"""
        return self.user_notifications.count()

    def get_unread_count(self):
        """Возвращает количество непрочитанных уведомлений"""
        return self.user_notifications.filter(is_read=False).count()


class NotificationsUsersThrough(models.Model):
    notification = models.ForeignKey(
        'Notifications',
        verbose_name=_("notification"),
        on_delete=models.CASCADE,
        related_name="user_notifications"
    )
    recipient = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_("recipient"),
        on_delete=models.CASCADE,
        related_name="notification_records"
    )

    is_read = models.BooleanField(_("is read"), default=False)
    received_at = models.DateTimeField(_("received at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Notification User Connection")
        verbose_name_plural = _("Notification User Connections")
        unique_together = ('notification', 'recipient')

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.recipient} - {self.notification.title} ({status})"

    def mark_as_read(self):
        """Помечает уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.save()

    @classmethod
    def get_unread_count_for_user(cls, user):
        """Возвращает количество непрочитанных уведомлений для пользователя"""
        return cls.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    def get_user_notifications(cls, user, is_read=None):
        """Возвращает уведомления пользователя с фильтром по статусу прочтения"""
        queryset = cls.objects.filter(recipient=user).select_related('notification')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        return queryset.order_by('-received_at')