import frappe
from frappe.model.document import Document
from red_line_sms.api.send_sms import send_sms_for_doc

class SendSMS(Document):
    def on_submit(self):
        send_sms_for_doc(self.name)
