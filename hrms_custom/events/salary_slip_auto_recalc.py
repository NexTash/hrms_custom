import frappe
from frappe.utils import flt

def auto_recalculate_dependent_components_after_insert(doc, method):
    """
    Hook that runs after salary slip insertion to recalculate
    dependent deduction components that need gross_year_to_date.
    """
    _recalculate_if_needed(doc, "after_insert")

def auto_recalculate_dependent_components_before_save(doc, method):
    """
    Hook that runs before salary slip save to recalculate
    dependent deduction components when earnings are modified.
    """
    # Only process if this is an update (not initial creation)
    if doc.is_new():
        return
        
    _recalculate_if_needed(doc, "before_save")

def _recalculate_if_needed(doc, trigger):
    """
    Common function to recalculate dependent components.
    """
    
    # Only process draft salary slips
    if doc.docstatus != 0:
        return
    
    # Define the dependent components that need recalculation
    dependent_components = [
        'IRS FUTA Employer Tax',
        'FDOR Reemployment Employer Tax'
    ]
    
    # Check if this salary slip has any dependent components
    has_dependent_components = False
    for deduction in doc.deductions:
        if deduction.salary_component in dependent_components:
            has_dependent_components = True
            break
    
    if not has_dependent_components:
        return
    
    # For before_save, check if any earnings changed
    if trigger == "before_save":
        earnings_changed = False
        
        # Get current earnings summary
        current_earnings = {}
        current_total_earnings = 0
        for earning in doc.earnings:
            current_earnings[earning.salary_component] = flt(earning.amount)
            current_total_earnings += flt(earning.amount)
        
        # Compare with previous state if available
        if hasattr(doc, "_doc_before_save"):
            old_earnings = {}
            old_total_earnings = 0
            for earning in doc._doc_before_save.earnings:
                old_earnings[earning.salary_component] = flt(earning.amount)
                old_total_earnings += flt(earning.amount)
            
            # Check if earnings changed
            if current_earnings != old_earnings or current_total_earnings != old_total_earnings:
                earnings_changed = True
        else:
            # If no previous state, assume earnings changed (safer approach)
            earnings_changed = True
        
        # Also check gross pay change as a fallback
        old_gross_pay = 0
        new_gross_pay = flt(doc.gross_pay)
        
        if hasattr(doc, "_doc_before_save"):
            old_gross_pay = flt(doc._doc_before_save.gross_pay)
        
        # Check if we should recalculate - either earnings changed or gross pay changed
        should_recalculate = earnings_changed or (new_gross_pay != old_gross_pay)
        
        if not should_recalculate:
            return
    
    # For after_insert, only recalculate if created from payroll entry
    if trigger == "after_insert":
        has_payroll_entry = bool(doc.payroll_entry)
        if not has_payroll_entry:
            return
    
    try:
        # Store the original amounts to check if they need updating
        original_amounts = {}
        for deduction in doc.deductions:
            if deduction.salary_component in dependent_components:
                original_amounts[deduction.salary_component] = deduction.amount
        
        # Store original income tax breakup values for comparison
        original_tax_values = {
            'ctc': getattr(doc, 'ctc', 0),
            'total_earnings': getattr(doc, 'total_earnings', 0),
            'non_taxable_earnings': getattr(doc, 'non_taxable_earnings', 0),
            'annual_taxable_amount': getattr(doc, 'annual_taxable_amount', 0),
            'income_tax_deducted_till_date': getattr(doc, 'income_tax_deducted_till_date', 0),
            'total_income_tax': getattr(doc, 'total_income_tax', 0)
        }
        
        # Use the recalculate method that updates document state
        doc.recalculate_dependent_components()
        
        # For after_insert, we need to actually update the database
        if trigger == "after_insert":
            
            # Update the main salary slip document - only use fields that exist in the table
            update_fields = {
                'gross_pay': doc.gross_pay,
                'total_deduction': doc.total_deduction,
                'net_pay': doc.net_pay,
                'modified': doc.modified,
                'modified_by': doc.modified_by
            }
            
            # Add only the tax fields that actually exist in the salary slip table
            existing_tax_fields = [
                'ctc', 'total_earnings', 'non_taxable_earnings', 'annual_taxable_amount',
                'income_tax_deducted_till_date', 'total_income_tax', 'current_month_income_tax',
                'future_income_tax_deductions', 'standard_tax_exemption_amount',
                'tax_exemption_declaration', 'deductions_before_tax_calculation'
            ]
            
            for field in existing_tax_fields:
                if hasattr(doc, field):
                    update_fields[field] = getattr(doc, field)
            
            # Build the SQL update query dynamically
            set_clause = ', '.join([f"`{field}` = %({field})s" for field in update_fields.keys()])
            update_fields['name'] = doc.name
            
            frappe.db.sql(f"""
                UPDATE `tabSalary Slip` 
                SET {set_clause}
                WHERE name = %(name)s
            """, update_fields)
            
            # Update the deduction details
            for deduction in doc.deductions:
                if deduction.salary_component in dependent_components:
                    frappe.db.sql("""
                        UPDATE `tabSalary Detail` 
                        SET amount = %(amount)s
                        WHERE parent = %(parent)s 
                        AND salary_component = %(salary_component)s
                        AND parentfield = 'deductions'
                    """, {
                        'amount': deduction.amount,
                        'parent': doc.name,
                        'salary_component': deduction.salary_component
                    })
            
            frappe.db.commit()
        
        # Check if any of the dependent components changed
        changes_made = False
        new_amounts = {}
        for deduction in doc.deductions:
            if deduction.salary_component in dependent_components:
                old_amount = original_amounts.get(deduction.salary_component, 0)
                new_amount = deduction.amount
                new_amounts[deduction.salary_component] = new_amount
                if old_amount != new_amount:
                    changes_made = True
                    frappe.logger().info(
                        f"Auto-recalculated {deduction.salary_component} for {doc.name}: {old_amount} -> {new_amount} (trigger: {trigger})"
                    )
        
        # Check if any tax values changed
        new_tax_values = {
            'ctc': getattr(doc, 'ctc', 0),
            'total_earnings': getattr(doc, 'total_earnings', 0),
            'non_taxable_earnings': getattr(doc, 'non_taxable_earnings', 0),
            'annual_taxable_amount': getattr(doc, 'annual_taxable_amount', 0),
            'income_tax_deducted_till_date': getattr(doc, 'income_tax_deducted_till_date', 0),
            'total_income_tax': getattr(doc, 'total_income_tax', 0)
        }
        
        tax_changes_made = False
        for field, old_value in original_tax_values.items():
            new_value = new_tax_values.get(field, 0)
            if old_value != new_value:
                tax_changes_made = True
                frappe.logger().info(
                    f"Auto-recalculated tax field {field} for {doc.name}: {old_value} -> {new_value} (trigger: {trigger})"
                )
        
        if changes_made or tax_changes_made:
            frappe.logger().info(f"Auto-recalculated dependent components and tax breakup for salary slip {doc.name} (trigger: {trigger})")
        
    except Exception as e:
        frappe.logger().error(f"Error in auto_recalculate_dependent_components for {doc.name} (trigger: {trigger}): {str(e)}")
        # Don't raise the error to avoid breaking the salary slip creation/saving
