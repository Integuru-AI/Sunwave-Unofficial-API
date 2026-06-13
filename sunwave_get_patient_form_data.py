import json
import random

def run(headers, user_input):
    """Retrieve the full data of a specific patient form instance, including all sections, fields, and signatures."""

    # Validate required inputs
    patient_id = user_input.get("patient_id")
    if not patient_id:
        return {"status_code": 400, "body": {"error": "patient_id is required"}}

    admission_id = user_input.get("admission_id")
    if not admission_id:
        return {"status_code": 400, "body": {"error": "admission_id is required"}}

    form_id = user_input.get("form_id")
    if not form_id:
        return {"status_code": 400, "body": {"error": "form_id is required"}}

    form_instance_id = user_input.get("form_instance_id")
    if not form_instance_id:
        return {"status_code": 400, "body": {"error": "form_instance_id is required"}}

    try:
        data = _fetch_form_data(headers, patient_id, admission_id, form_id, form_instance_id)
    except Exception as e:
        error_msg = str(e)
        if "Session expired" in error_msg or "401" in error_msg:
            return {"status_code": 401, "body": {"error": error_msg}}
        return {"status_code": 500, "body": {"error": error_msg}}

    # Parse sections and fields into a clean structure
    sections = []
    for sec in data.get("Sections", []):
        section_name = sec.get("SectionName", "")
        fields = []
        for col in sec.get("Columns", []):
            if isinstance(col, list):
                for field in col:
                    if isinstance(field, dict):
                        entry = {
                            "id": field.get("id", ""),
                            "label": field.get("label", ""),
                            "type": field.get("type", ""),
                            "value": field.get("value", ""),
                        }
                        if "name" in field:
                            entry["name"] = field["name"]
                        if "model" in field:
                            entry["model"] = field["model"]
                        if "uniqueId" in field:
                            entry["uniqueId"] = field["uniqueId"]
                        if "uuid" in field:
                            entry["uuid"] = field["uuid"]
                        if "list" in field:
                            entry["list"] = field["list"]
                        if "headers" in field:
                            entry["headers"] = field["headers"]
                        if "values" in field:
                            entry["values"] = field["values"]
                        if "placeholder" in field:
                            entry["placeholder"] = field["placeholder"]
                        for k, v in field.items():
                            if k.startswith("data"):
                                entry[k] = v
                        fields.append(entry)
            elif isinstance(col, dict):
                for field in col.get("Fields", []):
                    if isinstance(field, dict):
                        entry = {
                            "id": field.get("id", ""),
                            "label": field.get("label", ""),
                            "type": field.get("type", ""),
                            "value": field.get("value", ""),
                        }
                        if "name" in field:
                            entry["name"] = field["name"]
                        if "model" in field:
                            entry["model"] = field["model"]
                        if "uniqueId" in field:
                            entry["uniqueId"] = field["uniqueId"]
                        if "uuid" in field:
                            entry["uuid"] = field["uuid"]
                        if "list" in field:
                            entry["list"] = field["list"]
                        if "headers" in field:
                            entry["headers"] = field["headers"]
                        if "values" in field:
                            entry["values"] = field["values"]
                        if "placeholder" in field:
                            entry["placeholder"] = field["placeholder"]
                        for k, v in field.items():
                            if k.startswith("data"):
                                entry[k] = v
                        fields.append(entry)
        sections.append({
            "section_name": section_name,
            "fields": fields,
        })

    # Parse signatures
    signatures = []
    for sig in data.get("signatures", []):
        signatures.append({
            "date": sig.get("date", ""),
            "full_user_name": sig.get("full_user_name", ""),
            "signature_type": sig.get("signature_type", ""),
            "created_by": sig.get("created_by", ""),
        })

    result = {
        "form_id": data.get("formId"),
        "is_read_only": data.get("is_read_only", False),
        "is_revoked": data.get("isRevoked"),
        "datetime": data.get("datetime"),
        "showingUploadedFile": data.get("showingUploadedFile"),
        "uploadedFileContent": data.get("uploadedFileContent"),
        "group_id": data.get("group_id"),
        "signatures": signatures,
        "sections": sections,
    }

    return {"status_code": 200, "body": result}

# === PRIVATE ===

from curl_cffi import requests

BASE_URL = "https://emr.sunwavehealth.com"


def _fetch_form_data(headers, patient_id, admission_id, form_id, form_instance_id):
    """Fetch the form data from the API, including clinic_id resolution."""
    base_url = BASE_URL

    # Build Cookie header from cookie jar if available (jar has fresher cookies)
    cookie_jar = headers.get("__endgame_cookie_jar")
    if isinstance(cookie_jar, list):
        domain = "emr.sunwavehealth.com"
        cookie_parts = []
        for c in cookie_jar:
            c_domain = c.get("domain", "")
            if domain in c_domain or c_domain.lstrip(".") == domain:
                cookie_parts.append(f"{c['name']}={c['value']}")
        if cookie_parts:
            headers = dict(headers)
            headers["Cookie"] = "; ".join(cookie_parts)

    # Filter out non-string header values (e.g. internal metadata)
    headers = {k: v for k, v in headers.items() if isinstance(v, str)}

    # Generate a random sunwave_session_id (client-side random int 0-999999999)
    sunwave_session_id = str(random.randint(0, 999999999))

    # Fetch clinic_id from user profile
    profile_headers = {
        **headers,
        "Accept": "*/*",
        "sunwave_session_id": sunwave_session_id,
    }
    profile_resp = requests.get(
        f"{base_url}/SunwaveEMR/Processor/userProfile/",
        headers=profile_headers,
        impersonate="chrome131",
        timeout=30,
    )

    if profile_resp.status_code == 401:
        raise Exception("Session expired")

    if "login" in profile_resp.url.lower() and "userProfile" not in profile_resp.url:
        raise Exception("Session expired - redirected to login")

    if not profile_resp.text.strip():
        raise Exception("Session expired - empty profile response")

    try:
        profile_data = profile_resp.json()
    except Exception:
        raise Exception("Session expired - invalid profile response")

    clinic_id = str(profile_data.get("clinic_id", ""))

    # Build request headers
    req_headers = {
        **headers,
        "Accept": "*/*",
        "sunwave_session_id": sunwave_session_id,
        "Referer": f"{base_url}/SunwaveEMR/SunwaveClient/build/web/firsttabs.html",
    }
    if clinic_id:
        req_headers["clinic_id"] = clinic_id

    # Fetch the form data
    resp = requests.get(
        f"{base_url}/SunwaveEMR/Processor/PatientChart/",
        params={
            "mri": patient_id,
            "formId": form_id,
            "admission": admission_id,
            "formInstanceId": form_instance_id,
        },
        headers=req_headers,
        impersonate="chrome131",
        timeout=30,
    )

    if resp.status_code == 401:
        raise Exception("Session expired")

    if "login" in resp.url.lower() and "PatientChart" not in resp.url:
        raise Exception("Session expired - redirected to login")

    try:
        data = resp.json()
    except Exception:
        raise Exception(f"Failed to parse form data response (HTTP {resp.status_code})")

    if resp.status_code != 200:
        raise Exception(f"API returned HTTP {resp.status_code}: {json.dumps(data)}")

    return data
