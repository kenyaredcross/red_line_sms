import frappe
from frappe import _
from frappe.utils import now_datetime

from red_line_sms.utils.sms_utils import send_sms
from red_line_sms.utils.profile_utils import get_filtered_red_profiles

@frappe.whitelist()
def send_sms_for_doc(docname):
    doc = frappe.get_doc("Send SMS", docname)

    # if doc.status != "Draft":
    #     frappe.throw(_("SMS already sent or invalid status."))

    # if doc.workflow_status != "Approved":
    #     frappe.throw(_("Message(s) will be only sent upon full approval"))

    phones = []

    if doc.receiver_type == "Manual Entry":
        if not doc.phone_numbers:
            frappe.throw(_("No phone numbers entered."))
        phones = [x.strip() for x in doc.phone_numbers.split(",") if x.strip()]

    elif doc.receiver_type == "Red Profile":
        filters = {
            "counties": [x.county for x in doc.county],
            "contact_groups": [x.contact_group for x in doc.contact_group],
            # "tags": [x.tag for x in doc.tag],
            "projects": [x.project for x in doc.project],
            "tags": doc.tag or []
            # "projects": doc.project or []
        }
        red_profiles = get_filtered_red_profiles(filters)
        phones = [x.phone for x in red_profiles if x.phone]

    elif doc.receiver_type == "Contact":
        contacts = frappe.get_all("Contact", fields=["phone"])
        phones = [x.phone for x in contacts if x.phone]
    
    else:
        frappe.throw(_("Invalid recipient type."))

    if not phones:
        frappe.throw(_("No phone numbers found. SMS will not be sent."))

    # Sending ALL SMSs to Admin phone numbers -> I set this under "Redline SMS Settings" Doctype

    settings = frappe.get_single("RedLine SMS Settings")
    admin_phone_numbers = []

    if settings.admin_phone_numbers:
        admin_phone_numbers = [num.strip() for num in settings.admin_phone_numbers.split("\n") if num.strip()]
    
    phones = list({*phones, *admin_phone_numbers})

      

    # Send SMS
    response = send_sms(phones, doc.message)

    summary = response.get("summary", {})
    details = response.get("details", [])

    doc.set("delivery_log", [])  # clear previous logs
    doc.status = "Sent" if summary.get("success", 0) > 0 else "Failed"

    for d in details:
        doc.append("delivery_log", {
            "phone_number": d.get("number"),
            "status": d.get("status"),
            "status_code": d.get("status_code"),
            "cost": float(d["cost"].replace("KES", "").strip()) if d.get("cost") else 0.0,
            "message_id": d.get("message_id"),
            "timestamp": now_datetime()
        })

    doc.log = f"""\nSMS Summary:
  Total Recipients: {summary.get("total", 0)}
  Sent: {summary.get("success", 0)}
  Failed: {summary.get("failed", 0)}
  Blacklisted: {summary.get("blacklisted", 0)}
  Unknown: {summary.get("unknown", 0)}
  Total Cost: KES {summary.get("cost_total", 0.0):.2f}
"""
    doc.total_sent_sms = summary.get("total", 0)
    doc.total_cost = summary.get("cost_total", 0.0)
    doc.total_failed = summary.get("failed", 0)


    # ✅ Enable update after submit
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)

    return response
# Only Send SMS if Workflow has been fully approved

def workflow_send_sms_on_approval (doc, method = None):

    if doc.workflow_state == "Approved" and doc.status != "Sent":
        # Check if scheduled
        if doc.to_be_sent_on and doc.to_be_sent_on > now_datetime():
            doc.status = "Scheduled"

        doc.submit()                    