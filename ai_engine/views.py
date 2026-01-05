from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio

from .services import (
    get_group_psk_id,
    get_svvcms_app_ids,
    get_secret_key_for_uid,
    generate_access_token,
    call_mcp
)

from .langchain_engine import run_langchain
from .uid_resolver import resolve_uid_from_text
from .llm import general_llm_call   # Gemini-only fallback

import logging

logger = logging.getLogger(__name__)

def chat_ui(request):
    return render(request, "chat.html")


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request method"})

    user_input = request.POST.get("message", "").strip()
    if not user_input:
        return JsonResponse({"reply": "Please enter a message"})

    try:
        # -------------------------------------------------
        # 1️⃣ Try to detect NEW service from LOCAL JSON
        # -------------------------------------------------
        resolved = resolve_uid_from_text(user_input)

        if resolved:
            # 🔹 New service detected
            uid = resolved["uid"]
            service_name = resolved["service_name"]

            request.session["service_uid"] = uid
            request.session["service_name"] = service_name

            # ---- MCP FLOW ----
            group_psk_id = get_group_psk_id()
            app_ids = get_svvcms_app_ids(group_psk_id)
            secret_key = get_secret_key_for_uid(uid, app_ids)
            token = generate_access_token(secret_key)

            mcp_response = asyncio.run(call_mcp(uid, token))
            request.session["mcp_data"] = mcp_response

            reply = run_langchain(
                uid=uid,
                mcp_data=mcp_response,
                user_question=user_input
            )
            return JsonResponse({"reply": reply})

        # -------------------------------------------------
        # 2️⃣ CONTINUE EXISTING SERVICE (follow-up questions)
        # -------------------------------------------------
        uid = request.session.get("service_uid")
        mcp_data = request.session.get("mcp_data")

        if uid and mcp_data:
            reply = run_langchain(
                uid=uid,
                mcp_data=mcp_data,
                user_question=user_input
            )
            return JsonResponse({"reply": reply})

        # -------------------------------------------------
        # 3️⃣ GENERAL CHAT (Gemini only)
        # -------------------------------------------------
        reply = general_llm_call(user_input)
        return JsonResponse({"reply": reply})

    except Exception as e:

        logger.exception("Chat API Error")  # full traceback in terminal

        return JsonResponse({

            "reply": "Sorry, something went wrong. Please try again later."

        })

