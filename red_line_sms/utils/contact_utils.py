import frappe


def get_filtered_contacts(mapping_name, filters=None):
	"""
	Generic contact retrieval using SMS Contact Mapping.

	Args:
		mapping_name: Name of the SMS Contact Mapping record
		filters: list of dicts with keys: filter_field, filter_fieldtype, filter_doctype, filter_value

	Returns:
		List of dicts with phone (and optionally contact_name) from the source doctype
	"""
	mapping = frappe.get_doc("SMS Contact Mapping", mapping_name)

	source_doctype = mapping.source_doctype
	phone_field = mapping.phone_field
	name_field = mapping.name_field
	active_filter_field = mapping.active_filter_field
	active_filter_value = mapping.active_filter_value

	# Build fields to fetch
	fetch_fields = ["name", phone_field]
	if name_field:
		fetch_fields.append(name_field)

	# Build base filters
	base_filters = {}
	if active_filter_field and active_filter_value:
		# Try to cast to int if it looks like one (for Check fields)
		val = active_filter_value
		try:
			val = int(val)
		except (ValueError, TypeError):
			pass
		base_filters[active_filter_field] = val

	# Get all base records
	records = frappe.get_all(
		source_doctype,
		filters=base_filters,
		fields=fetch_fields,
		ignore_permissions=True,
		limit_page_length=0,
	)

	if not records:
		return []

	# Apply additional filters
	if filters:
		records_map = {r.name: r for r in records}

		for f in filters:
			field = f.get("filter_field")
			fieldtype = f.get("filter_fieldtype", "")
			filter_doctype = f.get("filter_doctype", "")
			value = f.get("filter_value", "")

			if not field or not value:
				continue

			values = [v.strip() for v in value.split(",") if v.strip()]

			if fieldtype == "Table MultiSelect":
				# Query the child table to find matching parents
				# filter_doctype here is the child table doctype name (the "options" of the Table MultiSelect)
				child_doctype = filter_doctype
				if not child_doctype:
					continue

				# Find the link field in the child table that's not "parent"
				child_meta = frappe.get_meta(child_doctype)
				link_fieldname = None
				for cf in child_meta.fields:
					if cf.fieldtype == "Link" and cf.fieldname != "parent":
						link_fieldname = cf.fieldname
						break

				if not link_fieldname:
					continue

				matched = frappe.get_all(
					child_doctype,
					filters={link_fieldname: ["in", values]},
					fields=["parent"],
					ignore_permissions=True,
					limit_page_length=0,
				)
				valid_parents = {m.parent for m in matched}
				records_map = {
					k: v for k, v in records_map.items() if k in valid_parents
				}

			else:
				# Direct field filter (Link, Select, Data, Check)
				if len(values) == 1:
					filter_val = values[0]
					# Try int cast for Check fields
					if fieldtype == "Check":
						try:
							filter_val = int(filter_val)
						except (ValueError, TypeError):
							pass
					records_map = {
						k: v for k, v in records_map.items()
						if str(v.get(field, "")) == str(filter_val)
					}
				else:
					records_map = {
						k: v for k, v in records_map.items()
						if str(v.get(field, "")) in values
					}

		records = list(records_map.values())

	# Only return records with a phone number
	results = []
	for r in records:
		phone = r.get(phone_field)
		if phone:
			entry = {"phone": phone}
			if name_field:
				entry["contact_name"] = r.get(name_field, "")
			results.append(entry)

	return results
