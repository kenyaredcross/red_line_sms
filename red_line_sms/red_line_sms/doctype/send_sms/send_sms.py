import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document
from red_line_sms.utils.sms_utils import send_sms

class SendSMS(Document):
    def on_submit(self):
        phones = []

        # Resolve recipient list
        if self.receiver_type == "Manual Entry":
            phones = [x.strip() for x in self.phone_numbers.split(",") if x.strip()]
        elif self.receiver_type == "Red Profile":
            red_profiles = frappe.get_all("Red Profile", filters={"enabled": 1}, fields=["phone"])
            phones = [x.phone for x in red_profiles if x.phone]
        elif self.receiver_type == "Contact":
            contacts = frappe.get_all("Contact", filters={}, fields=["phone"])
            phones = [x.phone for x in contacts if x.phone]

        if not phones:
            frappe.throw("No phone numbers found. SMS will not be sent.")

        response = send_sms(phones, self.message)

        self.set("delivery_log", [])
        self.status = "Failed"
        self.log = ""

        if "status" in response and response["status"] == "error":
            self.log = f"Error: {response['error']}"
        else:
            summary = response.get("summary", {})
            details = response.get("details", [])

            for d in details:
                self.append("delivery_log", {
                    "phone_number": d.get("number"),
                    "status": d.get("status"),
                    "status_code": d.get("status_code"),
                    "cost": float(d["cost"].replace("KES", "").strip()) if d.get("cost") else 0.0,
                    "message_id": d.get("message_id"),
                    "timestamp": now_datetime()
                })

            self.status = "Sent" if summary.get("success", 0) > 0 else "Failed"
            self.log = f"""\
SMS Summary:
  Total Recipients: {summary.get("total", 0)}
  Sent: {summary.get("success", 0)}
  Failed: {summary.get("failed", 0)}
  Blacklisted: {summary.get("blacklisted", 0)}
  Unknown: {summary.get("unknown", 0)}
  Total Cost: KES {summary.get("cost_total", 0.0):.2f}
"""

        # ✅ Ensure logs and child table persist
        self.flags.ignore_validate_update_after_submit = True
        self.save(ignore_permissions=True)
