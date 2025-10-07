from django.db import models
from django.core.validators import MinLengthValidator

from apps.utils import generate_random_string


class SymbolIdField(models.CharField):
    MIN_LENGTH = 16
    MAX_ATTEMPTS = 5

    def __init__(self, *args, **kwargs):
        kwargs["primary_key"] = True
        kwargs.setdefault("max_length", self.MIN_LENGTH)
        kwargs.setdefault("validators", []).append(
            MinLengthValidator(self.MIN_LENGTH)
        )
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add: # Выполняется только при СОЗДАНИИ нового объекта
            model_cls = model_instance.__class__
            new_id = None
            for _ in range(self.MAX_ATTEMPTS):
                new_id = self._generate_id(model_instance)
                if not model_cls.objects.filter(pk=new_id).exists():
                    setattr(model_instance, self.attname, new_id)
                    break
            if new_id is None:
                raise ValueError("Something went wrong, please try again.")

        return super().pre_save(model_instance, add)

    def _generate_id(self, model_instance):
        current_length = model_instance._meta.get_field(self.attname).max_length
        return generate_random_string(length=current_length)
