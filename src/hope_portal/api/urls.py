from django.urls import include, path

from .router import Router

app_name = "api"

router = Router()


urlpatterns = [
    path("", include(router.urls)),
]
