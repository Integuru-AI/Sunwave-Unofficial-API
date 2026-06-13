# Sunwave Unofficial API

Unofficial Python integrations for Sunwave.

## Integrations

- `sunwave_get_patient_form_data.py` - `get_patient_form_data` (853,757 live events).
- `sunwave_get_group_header_with_time.py` - `get_group_header_with_time` (194,723 live events).
- `sunwave_get_patient_admissions.py` - `get_patient_admissions` (6,662 live events).
- `sunwave_write_patient_chart_field.py` - `write_patient_chart_field` (6,361 live events).

## Usage

Each file exposes a `run(input, context)` entrypoint. The runtime is expected to provide:

- `input`: integration-specific request fields.
- `context["headers"]`: authenticated request headers when required.
- `context["base_url"]`: the platform base URL when overriding the default.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Info

This unofficial API is built by [Integuru.ai](https://integuru.ai/).

For custom requests or hosted authentication, contact richard@taiki.online.

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
