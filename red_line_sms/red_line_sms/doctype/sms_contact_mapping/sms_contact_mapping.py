import frappe
from frappe.model.document import Document


class SMSContactMapping(Document):
	def before_save(self):
		if not self.mapping_name and self.source_doctype:
			self.mapping_name = self.source_doctype
