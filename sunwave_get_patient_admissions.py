import random
from curl_cffi import requests


def run(headers, user_input):
    """Get the list of admissions for a patient."""
    base_url = BASE_URL

    # Validate input
    patient_id = user_input.get("patient_id")
    if not patient_id:
        return {"status_code": 400, "body": {"error": "patient_id is required"}}

    # Generate a random client-side session ID (mimics browser behavior)
    sunwave_session_id = str(random.randint(100000000, 999999999))

    # Fetch clinic_id from user profile
    profile_resp = requests.get(
        f"{base_url}/SunwaveEMR/Processor/userProfile/",
        headers={
            **headers,
            "Accept": "*/*",
            "sunwave_session_id": sunwave_session_id,
        },
        impersonate="chrome131",
        timeout=30,
    )

    if profile_resp.status_code == 200:
        try:
            profile_data = profile_resp.json()
        except Exception:
            # If we can't parse the profile, it may be a login redirect
            if "login" in profile_resp.url.lower() or "login" in profile_resp.text[:500].lower():
                return {"status_code": 401, "body": {"error": "Session expired"}}
            return {"status_code": 502, "body": {"error": "Failed to parse user profile"}}
    else:
        if profile_resp.status_code in (401, 403) or "login" in profile_resp.url.lower():
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {
            "status_code": profile_resp.status_code,
            "body": {"error": "Failed to fetch user profile"},
        }

    clinic_id = str(profile_data.get("clinic_id", ""))

    # Fetch admissions for the patient
    resp = requests.get(
        f"{base_url}/SunwaveEMR/Processor/loadAdmissions/?id={patient_id}",
        headers={
            **headers,
            "Accept": "*/*",
            "clinic_id": clinic_id,
            "sunwave_session_id": sunwave_session_id,
        },
        impersonate="chrome131",
        timeout=30,
    )

    if resp.status_code != 200:
        if resp.status_code in (401, 403) or "login" in resp.url.lower():
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {
            "status_code": resp.status_code,
            "body": {"error": "Failed to fetch admissions"},
        }

    try:
        data = resp.json()
    except Exception:
        if "login" in resp.text[:500].lower():
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {"status_code": 502, "body": {"error": "Invalid response from server"}}

    # Normalize output
    admissions = []
    for entry in data:
        admissions.append({
            "admission_id": entry.get("id", ""),
            "date": entry.get("date", ""),
            "time": entry.get("time", ""),
            "is_locked": entry.get("is_locked", "") != "",
        })

    return {"status_code": 200, "body": {"admissions": admissions}}
