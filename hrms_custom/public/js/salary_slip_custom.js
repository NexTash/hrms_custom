frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        // Add custom button as a primary button (not in dropdown)
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Recalculate Tax Deductions'), function() {
                frappe.call({
                    method: 'hrms_custom.utils.salary_utils.recalculate_all_deductions',
                    args: {
                        salary_slip_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.msgprint(__('Tax deductions recalculated successfully'));
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary'); // Make it a primary (blue) button
        }
    }
});
