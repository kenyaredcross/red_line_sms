import africastalking
import frappe

def get_credentials():
    return (
        frappe.conf.africastalking_username,
        frappe.conf.africastalking_api_key
    )

def init_africastalking():
    username, api_key = get_credentials()
    africastalking.initialize(username, api_key)
    return africastalking.SMS

def send_sms(phone_numbers, message, sender_id="REDCROSS"):
    try:
        sms = init_africastalking()
        response = sms.send(message, phone_numbers, sender_id)
        frappe.logger().info(f"SMS sent: {response}")
        return response
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Africa's Talking SMS Error")
        return {"status": "error", "error": str(e)}