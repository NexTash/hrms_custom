frappe.ui.form.on('Salary Detail', {
    salary_component: function(frm, cdt, cdn) {
        // When a salary component is selected, copy the flags from the salary component master
        var row = locals[cdt][cdn];
        if (row.salary_component) {
            frappe.db.get_value('Salary Component', row.salary_component, [
                'deduct_full_tax_on_selected_payroll_date', 
                'is_tax_applicable', 
                'is_flexible_benefit'
            ], function(r) {
                if (r && r.message) {
                    row.deduct_full_tax_on_selected_payroll_date = r.message.deduct_full_tax_on_selected_payroll_date || 0;
                    row.is_tax_applicable = r.message.is_tax_applicable || 0;
                    row.is_flexible_benefit = r.message.is_flexible_benefit || 0;
                    
                    // For components with full tax flag, ensure proper additional_amount setup
                    if (r.message.deduct_full_tax_on_selected_payroll_date && row.amount) {
                        // This is an additional salary component - set it up properly
                        row.additional_amount = row.amount;
                        row.default_amount = 0;
                        row.tax_on_additional_salary = 1;
                    } else {
                        // This is a regular salary component
                        row.additional_amount = 0;
                        row.default_amount = row.amount || 0;
                        row.tax_on_additional_salary = 0;
                    }
                    
                    // Refresh the form to show the updated values
                    frm.refresh_field('earnings');
                    frm.refresh_field('deductions');
                    
                    // Set flag for auto-recalculation
                    frm.doc._needs_auto_recalculation = true;
                }
            });
        }
    },
    
    amount: function(frm, cdt, cdn) {
        // When amount is changed, update additional_amount for components with full tax flag
        var row = locals[cdt][cdn];
        if (row.deduct_full_tax_on_selected_payroll_date && row.amount) {
            row.additional_amount = row.amount;
            row.default_amount = 0;
            row.tax_on_additional_salary = 1;
        } else if (row.amount) {
            row.additional_amount = 0;
            row.default_amount = row.amount;
            row.tax_on_additional_salary = 0;
        }
        
        frm.refresh_field('earnings');
        
        // Set flag for auto-recalculation
        frm.doc._needs_auto_recalculation = true;
    }
});

frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        // Add a custom button to manually trigger recalculation
        if (frm.doc.docstatus === 0 && frm.doc.name) {
            frm.add_custom_button(__('Recalculate Tax'), function() {
                frappe.call({
                    method: 'recalculate_dependent_components',
                    doc: frm.doc,
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                            frappe.show_alert({
                                message: __('Tax recalculation completed'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            });
        }
    }
});
