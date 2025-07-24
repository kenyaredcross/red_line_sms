import frappe
from frappe.utils.password import get_decrypted_password


def get_sms_settings():
    """
    Fetch Africa's Talking credentials from RedLine SMS Settings.
    Falls back to site_config.json if missing.
    """
    try:
        settings = frappe.get_single("RedLine SMS Settings")
        username = settings.username
        api_key = settings.api_key
        sender_id = settings.sender_id or "REDCROSS"
        
        # api_key = get_decrypted_password("RedLine SMS Settings", "api_key")

        if not (username and api_key):
            raise ValueError("Incomplete SMS Settings")

        return username, api_key, sender_id

    except Exception:
        # Fallback to site_config.json via frappe.conf
        return (
            frappe.conf.get("africastalking_username"),
            frappe.conf.get("africastalking_api_key"),
            frappe.conf.get("africastalking_sender_id", "REDCROSS")
        )


def init_africastalking():
    import africastalking

    username, api_key, _ = get_sms_settings()
    africastalking.initialize(username, api_key)
    return africastalking.SMS


def send_sms(phone_numbers, message, sender_id=None):
    """
    Send SMS to a list of phone numbers using Africa's Talking.
    Returns a dict with summary, detailed recipient logs, and raw response.
    """
    try:
        sms = init_africastalking()

        # Use default sender ID if not passed explicitly
        if not sender_id:
            _, _, sender_id = get_sms_settings()

        raw_response = sms.send(message, phone_numbers, sender_id)
        recipients = raw_response.get("SMSMessageData", {}).get("Recipients", [])

        summary = {
            "total": len(phone_numbers),
            "success": 0,
            "failed": 0,
            "blacklisted": 0,
            "unknown": 0,
            "cost_total": 0.0
        }

        detailed_log = []
        for r in recipients:
            status = r.get("status")
            code = r.get("statusCode")
            cost_str = r.get("cost", "KES 0.00")
            try:
                cost = float(cost_str.replace("KES", "").strip())
            except:
                cost = 0.0

            if status == "Success" or code == 100:
                summary["success"] += 1
            elif code in (400, 401):
                summary["blacklisted"] += 1
            elif code == 102:
                summary["failed"] += 1
            else:
                summary["unknown"] += 1

            summary["cost_total"] += cost

            detailed_log.append({
                "number": r.get("number"),
                "status": status,
                "status_code": code,
                "cost": cost_str,
                "message_id": r.get("messageId")
            })

        return {
            "summary": summary,
            "details": detailed_log,
            "raw": raw_response
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Africa's Talking SMS Error")
        return {"status": "error", "error": str(e)}
