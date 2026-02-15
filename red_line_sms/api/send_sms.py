import frappe
from frappe import _
from frappe.utils import now_datetime

from red_line_sms.utils.sms_utils import send_sms
from red_line_sms.utils.contact_utils import get_filtered_contacts

# System fields to exclude from filterable fields list
SYSTEM_FIELDS = {
	"name", "owner", "creation", "modified", "modified_by",
	"docstatus", "idx", "parent", "parentfield", "parenttype",
	"_user_tags", "_comments", "_assign", "_liked_by",
}

FILTERABLE_FIELDTYPES = {"Link", "Select", "Data", "Check", "Table MultiSelect"}


@frappe.whitelist()
def send_sms_for_doc(docname):
	doc = frappe.get_doc("Send SMS", docname)

	phones = []

	if doc.receiver_type == "Manual Entry":
		if not doc.phone_numbers:
			frappe.throw(_("No phone numbers entered."))
		phones = [x.strip() for x in doc.phone_numbers.split(",") if x.strip()]

	elif doc.contact_mapping:
		# Dynamic mapping-based retrieval
		filters = []
		for row in (doc.sms_filters or []):
			filters.append({
				"filter_field": row.filter_field,
				"filter_fieldtype": row.filter_fieldtype,
				"filter_doctype": row.filter_doctype,
				"filter_value": row.filter_value,
			})

		contacts = get_filtered_contacts(doc.contact_mapping, filters)
		phones = [c["phone"] for c in contacts if c.get("phone")]

	else:
		frappe.throw(_("Invalid recipient type or no contact mapping selected."))

	if not phones:
		frappe.throw(_("No phone numbers found. SMS will not be sent."))

	# Merge admin phone numbers from settings
	try:
		settings = frappe.get_single("RedLine SMS Settings")
		admin_phone_numbers = []
		if settings.admin_phone_numbers:
			admin_phone_numbers = [
				num.strip() for num in settings.admin_phone_numbers.split("\n") if num.strip()
			]
		phones = list({*phones, *admin_phone_numbers})
	except Exception:
		pass

	# Send SMS
	response = send_sms(phones, doc.message)

	summary = response.get("summary", {})
	details = response.get("details", [])

	doc.set("delivery_log", [])
	doc.status = "Sent" if summary.get("success", 0) > 0 else "Failed"

	for d in details:
		from red_line_sms.utils.sms_utils import sanitize_cost_currency

		doc.append("delivery_log", {
			"phone_number": d.get("number"),
			"status": d.get("status"),
			"status_code": d.get("status_code"),
			"cost": float(sanitize_cost_currency(d.get("cost", "").strip())) if d.get("cost") else 0.0,
			"message_id": d.get("message_id"),
			"timestamp": now_datetime(),
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

	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)

	return response


def workflow_send_sms_on_approval(doc, method=None):
	if doc.workflow_state == "Approved" and doc.status != "Sent":
		if doc.to_be_sent_on and doc.to_be_sent_on > now_datetime():
			doc.status = "Scheduled"
		doc.submit()


@frappe.whitelist()
def get_contact_count(mapping_name, filters=None):
	"""Return the count of matching contacts and estimated cost for preview."""
	import json

	if isinstance(filters, str):
		filters = json.loads(filters)

	contacts = get_filtered_contacts(mapping_name, filters or [])
	count = len(contacts)
	cost_per_sms = 0.50  # KES per SMS, default Africa's Talking rate
	estimated_cost = count * cost_per_sms

	return {
		"count": count,
		"estimated_cost": estimated_cost,
	}


@frappe.whitelist()
def get_filterable_fields(doctype_name):
	"""Return fields from a doctype that can be used as filters."""
	frappe.has_permission("SMS Contact Mapping", throw=True)

	meta = frappe.get_meta(doctype_name)
	result = []

	for field in meta.fields:
		if field.fieldname in SYSTEM_FIELDS:
			continue
		if field.fieldtype not in FILTERABLE_FIELDTYPES:
			continue

		entry = {
			"fieldname": field.fieldname,
			"label": field.label or field.fieldname,
			"fieldtype": field.fieldtype,
			"options": field.options or "",
		}

		if field.fieldtype == "Table MultiSelect" and field.options:
			# For Table MultiSelect, find the link doctype in the child table
			try:
				child_meta = frappe.get_meta(field.options)
				for cf in child_meta.fields:
					if cf.fieldtype == "Link" and cf.fieldname != "parent":
						entry["options"] = field.options
						entry["link_doctype"] = cf.options
						break
			except Exception:
				pass

		result.append(entry)

	return result
