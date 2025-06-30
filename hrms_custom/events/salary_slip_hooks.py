import frappe

def auto_recalculate_deductions(doc, method):
    """
    Automatically recalculate deductions when salary slip is saved,
    but only if explicitly flagged for recalculation.
    """
    # Only process if explicitly flagged for auto-recalculation
    # This flag will be set by frontend JavaScript when user makes manual changes
    if not getattr(doc, '_needs_auto_recalculation', False):
        return
        
    # Only process draft salary slips
    if doc.docstatus != 0:
        return
    
    # Clear the flag to prevent infinite loops
    doc._needs_auto_recalculation = False
    
    # Check if there are manual earnings that differ from structure defaults
    has_manual_earnings = False
    manual_earnings = {}
    
    if doc.earnings:
        for earning in doc.earnings:
            if hasattr(earning, 'amount') and earning.amount != 0:
                manual_earnings[earning.salary_component] = earning.amount
                has_manual_earnings = True
    
    # Only recalculate if we detect manual earnings
    if has_manual_earnings:
        # Clear existing calculations to start fresh
        doc.deductions = []
        doc.total_deduction = 0
        doc.net_pay = 0
        
        # Clear income tax breakup fields
        for field in ['total_earnings', 'ctc', 'previous_taxable_earnings_before_exemption', 
                     'current_structured_taxable_earnings_before_exemption', 
                     'future_structured_taxable_earnings_before_exemption']:
            if hasattr(doc, field):
                setattr(doc, field, 0)

        # Store manual earnings in a custom attribute
        doc._manual_earnings_override = manual_earnings

        # Monkey patch the eval_condition_and_formula method
        original_eval_method = doc.eval_condition_and_formula
        
        def patched_eval_condition_and_formula(struct_row, data):
            # If this is an earnings component with a manual override, use that amount
            if (hasattr(doc, '_manual_earnings_override') and 
                struct_row.salary_component in doc._manual_earnings_override):
                return doc._manual_earnings_override[struct_row.salary_component]
            
            # Otherwise, use the original calculation
            return original_eval_method(struct_row, data)
        
        # Apply the patch
        doc.eval_condition_and_formula = patched_eval_condition_and_formula

        try:
            # Recalculate only deductions (since earnings are already set manually)
            doc.calculate_component_amounts("deductions")
            doc.calculate_net_pay()
            
            # Restore the original method
            doc.eval_condition_and_formula = original_eval_method
            
        except Exception as e:
            # Restore the original method in case of error
            doc.eval_condition_and_formula = original_eval_method
            frappe.log_error(f"Error in auto_recalculate_deductions: {str(e)}")
            
        finally:
            # Clean up the temporary attribute
            if hasattr(doc, '_manual_earnings_override'):
                delattr(doc, '_manual_earnings_override')
