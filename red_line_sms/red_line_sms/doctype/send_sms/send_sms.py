import frappe
from frappe.model.document import Document
from red_line_sms.api.send_sms import send_sms_for_doc

class SendSMS(Document):
    def on_submit(self):
        send_sms_for_doc(self.name)
        

    # def on_update(self):

    #     if getattr(self, "workflow_state", None) == "Approved" and self.status != "Sent":
    #         frappe.logger().info(f'[SendSMS] Workflow approved for {self.name}, sending SMS')            
    #         send_sms_for_doc(self.name)

# class SendSMS(Document):
#     def before_submit(self):
#         # Enforce workflow approval prior to submission
#         if getattr(self, "workflow_state", None) != "Approved":
#             frappe.throw(_("Cannot submit before workflow approval. Current state: {0}")
#                          .format(self.workflow_state or "Unset"))

#     def on_submit(self):
#         # Redundant guard (belt-and-suspenders)
#         if getattr(self, "workflow_state", None) != "Approved":
#             frappe.throw(_("SMS can only be sent after workflow approval."))
#         # Defer to the API (which has its own checks & idempotency)
#         from red_line_sms.api.send_sms import send_sms_for_doc
#         send_sms_for_doc(self.name)
