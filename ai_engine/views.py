from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
from .utils import extract_uid

from .services import (
    get_group_psk_id,
    get_svvcms_app_ids,
    get_secret_key_for_uid,
    generate_access_token,
    call_mcp
)

from .langchain_engine import run_langchain


def chat_ui(request):
    return render(request, "chat.html")


@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        user_input = request.POST.get("message", "").strip()

        if not user_input:
            return JsonResponse({"reply": "Please enter a message"})

        try:
            # ----------------------------------
            # 1️⃣ Detect UID in message
            # ----------------------------------
            detected_uid = extract_uid(user_input)

            # ----------------------------------
            # 2️⃣ New UID found → MCP flow
            # ----------------------------------
            if detected_uid:
                uid = detected_uid

                group_psk_id = get_group_psk_id()
                app_ids = get_svvcms_app_ids(group_psk_id)
                secret_key = get_secret_key_for_uid(uid, app_ids)
                token = generate_access_token(secret_key)

                mcp_response = asyncio.run(call_mcp(uid, token))

                request.session["uid"] = uid
                request.session["mcp_data"] = mcp_response

                reply = run_langchain(
                    uid=uid,
                    mcp_data=mcp_response,
                    user_question="Summarize details"
                )

                return JsonResponse({"reply": reply})

            # ----------------------------------
            # 3️⃣ No UID → normal chat
            # ----------------------------------
            uid = request.session.get("uid")

            if not uid:
                return JsonResponse({
                    "reply": "Please provide your UID (e.g., svvcms26) to continue."
                })

            mcp_response = request.session.get("mcp_data", "")

            reply = run_langchain(
                uid=uid,
                mcp_data=mcp_response,
                user_question=user_input
            )

            return JsonResponse({"reply": reply})

        except Exception as e:
            return JsonResponse({"reply": f"❌ {str(e)}"})
