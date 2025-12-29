from django.urls import path
from .views import chat_ui, chat_api

urlpatterns = [
    path("", chat_ui, name="chat_ui"),
    path("api/chat/", chat_api, name="chat_api"),
]
