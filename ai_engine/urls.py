from django.urls import path
from .views import chat_ui, chat_api,pdf_chat_api

urlpatterns = [
    path("ai_assistant/", chat_ui, name="chat_ui"),
    path("api/chat/", chat_api, name="chat_api"),
    path("api/pdf-chat/", pdf_chat_api, name="pdf_chat_api"),  # ✅ NEW
]
