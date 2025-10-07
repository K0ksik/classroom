from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from apps.enums import Roles


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user_object(self, email, password, **extra_fields):
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        user = self._create_user_object(email, password, **extra_fields)
        user.save(using=self._db)
        return user

    async def _acreate_user(self, email, password, **extra_fields):
        """See _create_user()"""
        user = self._create_user_object(email, password, **extra_fields)
        await user.asave(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    create_user.alters_data = True

    async def acreate_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return await self._acreate_user(email, password, **extra_fields)

    acreate_user.alters_data = True

    def create_superuser(self, email, password=None, **extra_fields):

        admin_role_value = Roles.ADMIN.value
        extra_fields.setdefault("role_id", admin_role_value)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("role_id", None) != admin_role_value:
            raise ValueError("Superuser must have role=ADMIN.")
        if extra_fields.get("is_verified", None) is not True:
            raise ValueError("Superuser must have is_verified=True.")

        return self._create_user(email, password, **extra_fields)

    create_superuser.alters_data = True

    async def acreate_superuser(
            self, email, password=None, **extra_fields
    ):
        admin_role_value = Roles.ADMIN.value
        extra_fields.setdefault("role_id", admin_role_value)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("role_id", None) != admin_role_value:
            raise ValueError("Superuser must have role=ADMIN.")
        if extra_fields.get("is_verified", None) is not True:
            raise ValueError("Superuser must have is_verified=True.")

        return await self._acreate_user(email, password, **extra_fields)

    acreate_superuser.alters_data = True
