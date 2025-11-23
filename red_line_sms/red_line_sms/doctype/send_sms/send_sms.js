// Copyright (c) 2025, Kelvin NJenga and contributors
// For license information, please see license.txt

frappe.ui.form.on("Send SMS", {
	refresh(frm) {
        check_sms_length(frm);
	},
    validate: function (frm) {
        check_sms_length(frm);
        
    },
    message: function(frm) {
        check_sms_length(frm);
    }
});

function check_sms_length (frm) {
    if (frm.doc.message && frm.doc.message.length > 160){
             frappe.throw(__(`The SMS cannot exceed 160 characters, your current count is ${frm.doc.message.length}`));
        };
    
    if (frm.fields_dict.message && frm.fields_dict.message.$input) {
            frm.fields_dict.message.$input.on('input', function() {
                let current_length = $(this).val().length;
                let max_length = 160;
                let remaining = max_length - current_length;

                frm.set_intro(
                    `characters used: ${current_length}/ ${max_length}. Remaining: ${remaining >= 0 ? remaining : 0}`, 
                    remaining < 0 ? 'red' : 'blue'
                );
            });
        }
        
};


