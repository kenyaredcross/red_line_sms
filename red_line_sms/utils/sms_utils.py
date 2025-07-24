import frappe

def get_credentials():
    return (
        frappe.conf.africastalking_username,
        frappe.conf.africastalking_api_key
    )

def init_africastalking():
    # Import inside function to avoid breaking app installation
    import africastalking

    username, api_key = get_credentials()
    africastalking.initialize(username, api_key)
    return africastalking.SMS

def send_sms(phone_numbers, message, sender_id="REDCROSS"):
    """
    Sends SMS to a list of phone numbers using Africa's Talking.
    Returns a dict with summary, detailed recipient logs, and raw response.
    """
    try:
        sms = init_africastalking()
        raw_response = sms.send(message, phone_numbers, sender_id)

        recipients = raw_response.get("SMSMessageData", {}).get("Recipients", [])

        detailed_log = []
        summary = {
            "total": len(phone_numbers),
            "success": 0,
            "failed": 0,
            "blacklisted": 0,
            "unknown": 0,
            "cost_total": 0.0
        }

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
