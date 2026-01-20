from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
import logging

from .services import (
    get_group_psk_id,
    get_svvcms_app_ids,
    get_secret_key_for_uid,
    generate_access_token,
    call_mcp
)

from .langchain_engine import run_langchain
from .uid_resolver import resolve_service_from_text
from .llm import general_llm_call  # Gemini fallback

from django.core.files.storage import FileSystemStorage
from .rag_engine import query_uploaded_pdf

logger = logging.getLogger(__name__)


# ---------------------------
# Chat UI
# ---------------------------
def chat_ui(request):
    return render(request, "chat.html")


# ---------------------------
# Chat API
# ---------------------------
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request method"})

    user_input = request.POST.get("message", "").strip()
    if not user_input:
        return JsonResponse({"reply": "Please enter a message"})

    try:
        # ---------------------------
        # MCP Service Mode
        # ---------------------------
        resolved = resolve_service_from_text(user_input)
        if resolved:
            uid = resolved["uid"]
            service_name = resolved["service_name"]

            request.session["service_uid"] = uid
            request.session["service_name"] = service_name

            group_psk_id = get_group_psk_id()
            app_ids = get_svvcms_app_ids(group_psk_id)
            secret_key = get_secret_key_for_uid(uid, app_ids)
            token = generate_access_token(secret_key)

            mcp_response = asyncio.run(call_mcp(uid, token))
            request.session["mcp_data"] = mcp_response

            reply = run_langchain(uid=uid, mcp_data=mcp_response, user_question=user_input)
            return JsonResponse({"reply": reply})

        # ---------------------------
        # General Chat Fallback (Gemini)
        # ---------------------------
        reply = general_llm_call(user_input)
        return JsonResponse({"reply": reply})

    except Exception as e:
        logger.exception("Chat API Error")
        return JsonResponse({"reply": "❌ Sorry, something went wrong. Please try again later."})


@csrf_exempt
def pdf_chat_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request"})

    question = request.POST.get("question", "").strip()
    pdf = request.FILES.get("document")

    if not pdf or not question:
        return JsonResponse({"reply": "Please upload a PDF and ask a question"})

    fs = FileSystemStorage(location="media/ai_document_upload")
    file_path = fs.save(pdf.name, pdf)
    full_path = fs.path(file_path)

    try:
        # 1️⃣ Try PDF first
        pdf_answer = query_uploaded_pdf(full_path, question)

        if pdf_answer:
            return JsonResponse({"reply": pdf_answer})

        # 2️⃣ Fallback to MCP / Services
        resolved = resolve_service_from_text(question)
        if resolved:
            uid = resolved["uid"]
            service_name = resolved["service_name"]

            group_psk_id = get_group_psk_id()
            app_ids = get_svvcms_app_ids(group_psk_id)
            secret_key = get_secret_key_for_uid(uid, app_ids)
            token = generate_access_token(secret_key)

            mcp_response = asyncio.run(call_mcp(uid, token))
            reply = run_langchain(uid=uid, mcp_data=mcp_response, user_question=question)
            return JsonResponse({"reply": reply})

        # 3️⃣ Final fallback → Gemini
        reply = general_llm_call(question)
        return JsonResponse({"reply": reply})

    except Exception as e:
        logger.exception("PDF Chat Error")
        return JsonResponse({"reply": "❌ Failed to process request"})
