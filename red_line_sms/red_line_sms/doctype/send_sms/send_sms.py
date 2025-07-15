import frappe
from frappe.model.document import Document
from red_line_sms.utils.sms_utils import send_sms

class SendSMS(Document):
    def on_submit(self):
        phones = []

        if self.receiver_type == "Manual Entry":
            phones = [x.strip() for x in self.phone_numbers.split(",") if x.strip()]
        elif self.receiver_type == "Red Profile":
            red_profiles = frappe.get_all("Red Profile", filters={"enabled": 1}, fields=["phone"])
            phones = [x.phone for x in red_profiles if x.phone]
        elif self.receiver_type == "Contact":
            contacts = frappe.get_all("Contact", filters={}, fields=["phone"])
            phones = [x.phone for x in contacts if x.phone]

        if not phones:
            frappe.throw("No phone numbers found.")

        response = send_sms(phones, self.message)

        self.status = "Sent" if "Recipients" in response.get("SMSMessageData", {}) else "Failed"
        self.log = frappe.as_json(response)
