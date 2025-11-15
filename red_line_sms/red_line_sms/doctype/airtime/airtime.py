# Copyright (c) 2025, Kelvin NJenga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from red_line_sms.utils.airtime_utils import send_airtime


class Airtime(Document):
	def before_insert(self):

		if not self.total_amount:
			self.total_amount = 0.00
		if not self.total_sent:
			self.total_sent = 0
		if not self.total_discount:
			self.total_discount = 0.00


	def validate(self):

		if self.docstatus == 1:
			send_airtime(self.name)

	def on_submit(self):
		send_airtime(self.name)

