import frappe

from frappe.utils import strip_html

def sanitize_output(data):

    if isinstance(data, dict):
        return {key : sanitize_output(value) for key, value in data.items() }
    

    elif isinstance(data, list): 
        return [sanitize_output(i) for i in data]

    elif isinstance(data, str):
        return strip_html(data).strip()

@frappe.whitelist(allow_guest = False)
def get_sms_data(limit = 100):

    try:
        limit = int(limit)


        sms_data = frappe.db.get_all(
            "Send SMS", 
            fields = ["name", "created_by", "created_on", "to_be_sent_on", "workflow_state", "status",
                "receiver_type", "phone_numbers", "message",
                 "log", "total_sent_sms",
                "total_failed", "total_cost",
            ],
            limit = limit, 
            order_by="modified desc"
        )

        for log in sms_data:
            
            log["delivery_log"] = frappe.db.get_all(
                "SMS Log Detail", 
                filters = {"parent": log["name"]},
                fields = ["phone_number", "status", "cost", "status_code", "message_id", "timestamp",
                    ]
            )
        

        sms_data = sanitize_output(sms_data)

        return {"success": True, "data": sms_data}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API ")
        return {"success": False, "error": str(e)}

    



    