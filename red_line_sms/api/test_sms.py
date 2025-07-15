import frappe
from frappe import whitelist
from red_line_sms.utils.sms_utils import send_sms

@frappe.whitelist(allow_guest=True)  # <== This is what makes it callable via REST
def test_sms():
    return send_sms(["+254715150220"], "Test SMS from Red Line System")
