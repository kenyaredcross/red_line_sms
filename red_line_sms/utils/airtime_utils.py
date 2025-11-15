import frappe
from frappe.utils.password import get_decrypted_password
import africastalking

def get_airtime_settings():

    try:
        settings = frappe.get_single("RedLine SMS Settings")        
        username = settings.username
        api_key = settings.api_key
        
        if not (username and api_key):
            raise ValueError("Incomplete Settings")
        
        return username, api_key
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_airtime_settings")
        return None, None



def init_africastalking():
    username, api_key = get_airtime_settings()
    africastalking.initialize(username, api_key)

    return africastalking.Airtime

@frappe.whitelist()
def send_airtime(docname):
    airtime = init_africastalking()

    doc = frappe.get_doc("Airtime", docname)

    phone_number = doc.phone
    amount = str(doc.amount)
    currency_code = "KES"

    try:
        response = airtime.send(
            phone_number=phone_number,
            amount=amount,
            currency_code=currency_code,
        )

         
        frappe.msgprint(str(response))
        return response
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Airtime Send Error: {docname}")
        frappe.throw(f"Encountered Error: {str(e)}")



        