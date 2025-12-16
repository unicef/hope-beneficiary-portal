from django.db import models

from ._base import HopeModel


class HopeUser(HopeModel):
    id = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True, null=True)
    is_staff = models.BooleanField(default=False, null=True)
    is_superuser = models.BooleanField(default=False, null=True)
    date_joined = models.DateTimeField(null=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Routing:
        key = "hope"

    class Meta(HopeModel.Meta):
        db_table = "core_user"

    class Tenant:
        tenant_filter_field: str = "__all__"

    def __str__(self) -> str:
        return self.username or str(self.id)
