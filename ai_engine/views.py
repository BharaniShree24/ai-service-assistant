from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
from .services import *


# Home page
def chat_ui(request):
    return render(request, "chat.html")


# API endpoint for chat
@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        uid = request.POST.get("message")
        if not uid:
            return JsonResponse({"reply": "UID is required"})

        try:
            group_psk_id = get_group_psk_id()
            app_ids = get_svvcms_app_ids(group_psk_id)
            secret_key = get_secret_key_for_uid(uid, app_ids)
            token = generate_access_token(secret_key)

            raw_result = asyncio.run(call_mcp(uid, token))
            summary = asyncio.run(summarize_with_gemini(raw_result))

            return JsonResponse({"reply": summary})

        except Exception as e:
            return JsonResponse({"reply": f"Error: {str(e)}"})
    return JsonResponse({"error": "Invalid request"}, status=400)