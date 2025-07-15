import frappe
from frappe import _

from red_line_sms.utils.sms_utils import send_sms

@frappe.whitelist()
def send_sms_for_doc(docname):
    doc = frappe.get_doc("Send SMS", docname)
    
    if doc.status != "Draft":
        frappe.throw(_("SMS already sent or invalid status."))

    phones = []
    if doc.receiver_type == "Manual Entry":
        phones = [x.strip() for x in doc.phone_numbers.split(",") if x.strip()]
    elif doc.receiver_type == "Red Profile":
        red_profiles = frappe.get_all("Red Profile", filters={"enabled": 1}, fields=["phone"])
        phones = [x.phone for x in red_profiles if x.phone]
    elif doc.receiver_type == "Contact":
        contacts = frappe.get_all("Contact", filters={}, fields=["phone"])
        phones = [x.phone for x in contacts if x.phone]

    if not phones:
        frappe.throw(_("No phone numbers found."))

    response = send_sms(phones, doc.message)

    doc.status = "Sent" if "Recipients" in response.get("SMSMessageData", {}) else "Failed"
    doc.log = frappe.as_json(response)
    doc.save(ignore_permissions=True)
    return response
