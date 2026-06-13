from curl_cffi import requests

try:
    _base = BASE_URL
except NameError:
    _base = "https://emr.sunwavehealth.com"


def run(headers, user_input):
    """Get group header with patient time information for a group note."""

    # Validate required inputs
    group_id = user_input.get("group_id")
    if not group_id:
        return {"status_code": 400, "body": {"error": "group_id is required"}}

    form_instance_id = user_input.get("form_instance_id")
    if not form_instance_id:
        return {"status_code": 400, "body": {"error": "form_instance_id is required"}}

    try:
        data = _call_api(group_id, form_instance_id, headers)
    except RuntimeError as e:
        msg = str(e)
        if "Session expired" in msg:
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {"status_code": 500, "body": {"error": msg}}
    except Exception as e:
        return {"status_code": 500, "body": {"error": str(e)}}

    return {
        "status_code": 200,
        "body": {
            "group_title": data.get("group_title", ""),
            "session_date": data.get("session_date", ""),
            "started": data.get("started", ""),
            "ended": data.get("ended", ""),
            "duration": data.get("duration", ""),
            "patient_time_started": data.get("patient_time_started", ""),
            "patient_time_ended": data.get("patient_time_ended", ""),
            "patient_time_duration": data.get("patient_time_duration", ""),
            "group_objectives": data.get("group_objectives", ""),
            "service_facility_id": data.get("service_facility_id", ""),
            "title_read_only": data.get("title_read_only", ""),
            "objectives_can_be_edited": data.get("objectives_can_be_edited", ""),
            "display_group_title_list": data.get("display_group_title_list", ""),
            "disable_group_title_description": data.get("disable_group_title_description", ""),
        },
    }


# === PRIVATE ===


def _call_api(group_id, form_instance_id, headers):
    """Fetch group header with patient time from the API."""
    base_url = _base

    response = requests.get(
        f"{base_url}/SunwaveEMR/Processor/groupHeaderWithPatientTime/",
        params={
            "group_id": group_id,
            "form_instance_id": form_instance_id,
        },
        headers={
            **headers,
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        impersonate="chrome131",
        timeout=30,
    )

    # Detect expired session
    if response.status_code in (401, 403):
        raise RuntimeError("Session expired")
    if response.status_code == 302 or (
        response.status_code == 200
        and "text/html" in response.headers.get("Content-Type", "")
        and "<html" in response.text[:500].lower()
    ):
        raise RuntimeError("Session expired")

    if response.status_code != 200:
        raise RuntimeError(f"Request failed with status {response.status_code}")

    return response.json()
