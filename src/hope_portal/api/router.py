from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import APIRootView, DefaultRouter


class RootView(APIRootView):
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.user.is_authenticated:
            return super().get(request, *args, **kwargs)
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)


class Router(DefaultRouter):
    APIRootView = RootView
