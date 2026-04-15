from django.urls import include, path

from . import views

app_name = "ui"

urlpatterns = [
    path("", views.HomeView.as_view(), name="index"),
    path("flow/", include("hope_portal.ui.views.flow.urls", namespace="flow")),
    path("errors/400/", views.handler400, name="errors-400"),
    path("errors/403/", views.handler403, name="errors-403"),
    path("errors/404/", views.handler404, name="errors-404"),
    path("errors/500/", views.handler500, name="errors-500"),
    path("healthcheck/", views.HealthCheckView.as_view(), name="healthcheck"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("locked-out/", views.LockedOutView.as_view(), name="locked_out"),
]
