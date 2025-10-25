import frappe
from frappe.utils import now_datetime
from red_line_sms.api.send_sms import send_sms_for_doc

def process_scheduled_sms():

    now = now_datetime()


    scheduled_sms = frappe.get_all(
        "Send SMS",
        filters = {
            "workflow_state" : "Approved",
            "status" : "Scheduled",
            "to_be_sent_on" : ["<=", now]
        },
        fields = ["name"]
    )

    for sms in scheduled_sms:
        try:
            doc = frappe.get_doc("Send SMS", sms.name)
            frappe.logger().info(f"Sending Scheduled SMS: {doc.name}")
            send_sms_for_doc(doc.name)
            doc.status = "Sent"
            frappe.db.commit()
            doc.save(ignore_permissions = True)            
        except Exception as e:
            frappe.logger().error(f"Failed to send scheduled sms {sms.name}: {e}")