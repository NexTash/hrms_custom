frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        // Add Regenerate Salary Slip button
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.add_custom_button(__('Regenerate Salary Slip'), function() {
                frappe.call({
                    doc: frm.doc,
                    method: 'regenerate_salary_slip',
                    callback: function() {
                        frm.refresh();
                    }
                });
            });
        }
        
        // Add Recalculate Tax Deductions button
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Recalculate Tax Deductions'), function() {
                frappe.call({
                    method: 'hrms_custom.utils.salary_utils.recalculate_all_deductions',
                    args: {
                        salary_slip_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: __('Tax deductions recalculated successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary'); // Make it a primary (blue) button
        }
    }
});
