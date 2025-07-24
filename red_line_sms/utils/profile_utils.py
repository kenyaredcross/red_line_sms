import frappe

def get_filtered_red_profiles(filters, user=None):
    # Base filter: Only active Red Profiles
    base_profiles = frappe.get_all(
        "Red Profile",
        filters={"is_active": 1},
        fields=["name", "phone", "county"],
        ignore_permissions=True
    )

    if not base_profiles:
        return []

    red_profiles_map = {p.name: p for p in base_profiles}

    # --- COUNTY filter ---
    if filters.get("counties"):
        county_names = []
        for row in filters["counties"]:
            if isinstance(row, dict) and row.get("county"):
                county_names.append(row["county"])
            elif isinstance(row, str):
                county_names.append(row)
        county_names = [c for c in county_names if c]

        if county_names:
            # Filter Red Profiles directly, since their `county` field is a Link
            red_profiles_map = {
                k: v for k, v in red_profiles_map.items()
                if v.get("county") in county_names
            }

    # --- CONTACT GROUP filter ---
    if filters.get("contact_groups"):
        group_names = []
        for row in filters["contact_groups"]:
            if isinstance(row, dict) and row.get("contact_group"):
                group_names.append(row["contact_group"])
            elif isinstance(row, str):
                group_names.append(row)
        group_names = [g for g in group_names if g]

        if group_names:
            members = frappe.get_all(
                "Red Profile Group Membership",
                filters={"contact_group": ["in", group_names]},
                fields=["parent"]  # parent = Red Profile
            )
            valid_names = {x.parent for x in members}
            red_profiles_map = {
                k: v for k, v in red_profiles_map.items() if k in valid_names
            }


    # --- PROJECT filter ---
    if filters.get("projects"):
        project_names = [x.project for x in filters["projects"] if x.project]
        if project_names:
            matched_profiles = frappe.get_all(
                "Project Link",
                filters={"project": ["in", project_names]},
                fields=["parent"]
            )
            valid_names = {x.parent for x in matched_profiles}
            red_profiles_map = {
                k: v for k, v in red_profiles_map.items() if k in valid_names
            }
    

    
    # --- TAG filter ---
    if filters.get("tags"):
        tag_names = [x.tag for x in filters["tags"] if x.tag]
        if tag_names:
            tag_links = frappe.get_all(
                "Red Profile Tag",
                filters={"tag": ["in", tag_names]},
                fields=["parent"]
            )
            valid_names = {x.parent for x in tag_links}
            red_profiles_map = {
                k: v for k, v in red_profiles_map.items() if k in valid_names
            }

    # --- Only keep profiles with phone numbers ---
    final_profiles = [
        profile for profile in red_profiles_map.values()
        if profile.get("phone")
    ]

    return final_profiles
