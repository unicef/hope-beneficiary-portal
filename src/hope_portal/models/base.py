from django.db import models


class BaseQuerySet(models.QuerySet[models.Model]):
    pass


class BaseManager(models.Manager[models.Model]):
    _queryset_class = BaseQuerySet


class AbstractModel(models.Model):
    last_modify_date = models.DateTimeField(auto_now=True)

    objects = BaseManager()

    class Meta:
        abstract = True
        app_label = "hope_portal"
