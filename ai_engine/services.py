import asyncio
import json
import requests
from fastmcp import Client as MCPClient
import google.generativeai as genai

BASE_URL = "https://api.nanoxlabs.com"
AUTH_URL = f"{BASE_URL}/auth/token"
MCP_URL = f"{BASE_URL}/coreapi/mcp"
GEMINI_API_KEY = "AIzaSyAR8soMHRvaKOjArlvxiPzTpwgVylNlz0E"
GROUP_ID = "svvcms"


# STEP 1: GET svvcms GROUP PSK_ID

def get_group_psk_id():
    response = requests.post(
        AUTH_URL,
        json={"secret_key": "O1eb30Fi9K8W7omT26vdVMzokpEvYxQZ"},
        timeout=10
    )
    response.raise_for_status()
    token_data = response.json()
    auth_header = f"{token_data['token_type']} {token_data['access_token']}"

    url = (
        f"{BASE_URL}/getapi/rest/v1/auth/"
        "all_fields/api_studio_app_group/all?response_format=json"
    )
    response = requests.get(url, headers={"Authorization": auth_header}, timeout=10)
    response.raise_for_status()
    groups = response.json().get("data", [])
    group = next((g for g in groups if g.get("group_id") == GROUP_ID), None)
    if not group:
        raise Exception("❌ svvcms group not found")
    return group["psk_id"]


# STEP 2: GET ALL svvcms APP IDS
def get_svvcms_app_ids(group_psk_id):
    response = requests.post(
        AUTH_URL,
        json={"secret_key": "NUvE3Fzqq5S3MAuTQ2kMEtBS2Jqb2tD4"},
        timeout=10
    )
    response.raise_for_status()
    token_data = response.json()
    auth_header = f"{token_data['token_type']} {token_data['access_token']}"

    url = f"{BASE_URL}/getapi/rest/v1/auth/api_studio_app_name?response_format=json"
    payload = {
        "queries": [{"field": "api_studio_app_group_id", "value": group_psk_id, "operation": "equal"}],
        "search_type": "all"
    }
    response = requests.get(url, json=payload, headers={"Authorization": auth_header}, timeout=10)
    response.raise_for_status()
    apps = response.json().get("data", [])
    return [app["app_id"] for app in apps]


# STEP 3: GET SECRET KEY FOR UID
def get_secret_key_for_uid(uid, valid_app_ids):
    if uid not in valid_app_ids:
        raise Exception("❌ UID not part of svvcms group")

    response = requests.get(f"{BASE_URL}/auth/api/tokens/", timeout=10)
    response.raise_for_status()
    tokens = response.json()
    token_record = next((t for t in tokens if t.get("uid") == uid and t.get("active") is True), None)
    if not token_record:
        raise Exception("❌ No active token found for UID")
    return token_record["secret_key"]


# STEP 4: GENERATE ACCESS TOKEN
def generate_access_token(secret_key):
    res = requests.post(AUTH_URL, json={"secret_key": secret_key}, timeout=10)
    res.raise_for_status()
    print("🔐 Token Generated Successfully")
    return res.json()["access_token"]


# STEP 5: MCP CALL
async def call_mcp(uid, token):
    async with MCPClient(MCP_URL, auth=token) as client:
        print(f"✅ MCP Connected for UID: {uid}")
        payload = {"uid": uid, "data": {}}
        result = await client.call_tool("post_execute_python_file", payload)
        content = getattr(result, "content", None)
        text = content[0].text if content else str(result)
        print("📥 Raw MCP Response:", text)
        return text


# STEP 6: GEMINI SUMMARY
async def summarize_with_gemini(text):

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    response = await model.generate_content_async(
        "Summarize this MCP service data in clean bullet points:\n\n" + text
    )
    return response.text

