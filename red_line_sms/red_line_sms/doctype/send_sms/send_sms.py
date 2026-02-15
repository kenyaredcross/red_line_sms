import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from red_line_sms.api.send_sms import send_sms_for_doc


class SendSMS(Document):
    def validate(self):
        # Dynamically allow receiver_type values from SMS Contact Mapping
        if self.receiver_type and self.receiver_type != "Manual Entry":
            valid_options = ["Manual Entry"]
            mappings = frappe.get_all(
                "SMS Contact Mapping", pluck="mapping_name", ignore_permissions=True
            )
            valid_options.extend(mappings)

            if self.receiver_type in valid_options:
                # Inject the option into the field meta so Frappe validation passes
                meta = frappe.get_meta(self.doctype)
                field = meta.get_field("receiver_type")
                if field:
                    field.options = "\n".join(valid_options)

    def on_submit(self):
        if not self.to_be_sent_on or self.to_be_sent_on <= now_datetime():
            frappe.logger().info(f"Submitting {self.name}: sending SMS immediately.")
            send_sms_for_doc(self.name)
        else:
            frappe.logger().info(f"Submitting {self.name}: scheduled for {self.to_be_sent_on}")

        # send_sms_for_doc(self.name) 
        

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
