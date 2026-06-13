import json
import random
from curl_cffi import requests

BASE_URL = "https://emr.sunwavehealth.com"


def run(headers, user_input):
    """Write a value to a specific field on a patient chart form."""

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

    field_id = user_input.get("field_id")
    if field_id is None:
        return {"status_code": 400, "body": {"error": "field_id is required"}}

    value = user_input.get("value", "")

    # Optional fields
    field_type = user_input.get("type", "")
    master_field = user_input.get("master_field", "")
    reportable_field = user_input.get("reportable_field", "null")
    radio_value = user_input.get("radioValue")
    checkbox_value = user_input.get("checkboxValue")
    row = user_input.get("row")
    col = user_input.get("col")
    data = user_input.get("data")

    try:
        result = _write_field(
            headers=headers,
            patient_id=patient_id,
            admission_id=admission_id,
            form_id=form_id,
            form_instance_id=form_instance_id,
            field_id=field_id,
            value=value,
            field_type=field_type,
            master_field=master_field,
            reportable_field=reportable_field,
            radio_value=radio_value,
            checkbox_value=checkbox_value,
            row=row,
            col=col,
            data=data,
        )
        return result
    except Exception as e:
        return {"status_code": 500, "body": {"error": str(e)}}


# === PRIVATE ===


def _write_field(headers, patient_id, admission_id, form_id, form_instance_id, field_id, value, field_type, master_field, reportable_field, radio_value=None, checkbox_value=None, row=None, col=None, data=None):
    """Execute the field write against the patient chart API."""

    # Step 1: Get clinic_id from userProfile
    profile_resp = requests.get(
        f"{BASE_URL}/SunwaveEMR/Processor/userProfile/",
        headers=headers,
        impersonate="chrome131",
        timeout=30,
    )

    if profile_resp.status_code != 200:
        # Check for auth failure
        if profile_resp.status_code in (401, 403) or "login" in profile_resp.url.lower():
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {"status_code": profile_resp.status_code, "body": {"error": "Failed to fetch user profile"}}

    try:
        profile_data = profile_resp.json()
    except Exception:
        # If response is not JSON, likely a login redirect
        if "login" in profile_resp.text.lower() or "j_security_check" in profile_resp.text.lower():
            return {"status_code": 401, "body": {"error": "Session expired"}}
        return {"status_code": 500, "body": {"error": "Invalid user profile response"}}

    clinic_id = profile_data.get("clinic_id", "")
    if not clinic_id:
        return {"status_code": 500, "body": {"error": "Could not determine clinic_id from user profile"}}

    # Step 2: Generate sunwave_session_id (random client identifier)
    sunwave_session_id = str(random.randint(0, 999999999))

    # Step 3: Build the request
    params = {
        "patient_id": str(patient_id),
        "admission_id": str(admission_id),
        "form_id": str(form_id),
        "form_instance_id": str(form_instance_id),
        "reportable_field": reportable_field,
        "field_id": str(field_id),
        "type": field_type,
        "masterField": master_field,
    }

    request_headers = {
        **headers,
        "Content-Type": "text/plain;charset=UTF-8",
        "Accept": "*/*",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/SunwaveEMR/SunwaveClient/build/web/firsttabs.html",
        "clinic_id": str(clinic_id),
        "sunwave_session_id": sunwave_session_id,
    }

    # Step 4: Build the POST body
    # For yes/no radio fields, the body is JSON with radioValue included
    # For textareaWithNone fields, the body is JSON with checkboxValue included
    # For table operations, the body is JSON with row/col included
    if radio_value is not None:
        body_payload = {
            "type": field_type,
            "uniqueId": str(field_id),
            "radioValue": radio_value,
            "value": str(value),
        }
        post_body = json.dumps(body_payload, separators=(",", ":"))
    elif checkbox_value is not None:
        body_payload = {
            "uniqueId": str(field_id),
            "type": field_type,
            "checkboxValue": checkbox_value,
            "value": str(value),
        }
        post_body = json.dumps(body_payload, separators=(",", ":"))
    elif field_type == "painScale":
        body_payload = {
            "selected-value": str(value),
            "type": "painScale",
            "uniqueId": str(field_id),
        }
        post_body = json.dumps(body_payload, separators=(",", ":"))
    elif field_type == "multiselect_checkboxes":
        body_payload = {
            "uniqueId": str(field_id),
            "type": "multiselect_checkboxes",
            "data": data if data is not None else [],
        }
        post_body = json.dumps(body_payload, separators=(",", ":"))
    elif field_type == "multicolumn_assessment":
        body_payload = {
            "uniqueId": str(field_id),
            "type": "multicolumn_assessment",
            "value": value if isinstance(value, dict) else value,
        }
        post_body = json.dumps(body_payload, separators=(",", ":"))
    elif field_type in ("table.addRow", "table.delete", "table.edit"):
        body_payload = {
            "uniqueId": str(field_id),
            "type": field_type,
        }
        if row is not None:
            body_payload["row"] = str(row)
        if col is not None:
            body_payload["col"] = str(col)
        if field_type == "table.edit":
            body_payload["value"] = str(value)
        post_body = json.dumps(body_payload, separators=(",", ":"))
    else:
        post_body = str(value)

    # Step 5: POST the value
    response = requests.post(
        f"{BASE_URL}/SunwaveEMR/Processor/PatientChart/",
        params=params,
        data=post_body,
        headers=request_headers,
        impersonate="chrome131",
        timeout=30,
    )

    # Check for auth failure
    if response.status_code in (401, 403):
        return {"status_code": 401, "body": {"error": "Session expired"}}
    if response.status_code == 302 or (response.status_code == 200 and "j_security_check" in response.text):
        return {"status_code": 401, "body": {"error": "Session expired"}}

    # Return result
    try:
        body = response.json()
    except Exception:
        body = response.text

    return {"status_code": response.status_code, "body": body}
