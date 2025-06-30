import frappe

@frappe.whitelist()
def recalculate_all_deductions(salary_slip_name):
    """
    Recalculates all salary components by providing manual earnings amounts
    to the formula evaluation context, avoiding the override-addition problem.
    """
    try:
        # Get the salary slip document
        salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)
        
        if salary_slip.docstatus != 0:
            frappe.throw("Can only recalculate for draft salary slips")

        # Store current manual earnings values before clearing
        manual_earnings = {}
        for earning in salary_slip.earnings:
            if hasattr(earning, 'amount') and earning.amount != 0:
                manual_earnings[earning.salary_component] = earning.amount

        # Clear existing calculations
        salary_slip.earnings = []
        salary_slip.deductions = []
        salary_slip.total_earning = 0
        salary_slip.total_deduction = 0
        salary_slip.gross_pay = 0
        salary_slip.net_pay = 0
        
        # Clear income tax breakup fields
        for field in ['total_earnings', 'ctc', 'previous_taxable_earnings_before_exemption', 
                     'current_structured_taxable_earnings_before_exemption', 
                     'future_structured_taxable_earnings_before_exemption']:
            if hasattr(salary_slip, field):
                setattr(salary_slip, field, 0)

        # Store manual earnings in a custom attribute that can be accessed during calculation
        salary_slip._manual_earnings_override = manual_earnings

        # Monkey patch the eval_condition_and_formula method to use manual amounts
        original_eval_method = salary_slip.eval_condition_and_formula
        
        def patched_eval_condition_and_formula(struct_row, data):
            # If this is an earnings component with a manual override, use that amount
            if (hasattr(salary_slip, '_manual_earnings_override') and 
                struct_row.salary_component in salary_slip._manual_earnings_override):
                return salary_slip._manual_earnings_override[struct_row.salary_component]
            
            # Otherwise, use the original calculation
            return original_eval_method(struct_row, data)
        
        # Apply the patch
        salary_slip.eval_condition_and_formula = patched_eval_condition_and_formula

        # Now process the salary structure with manual earnings considered
        if not salary_slip.salary_slip_based_on_timesheet:
            salary_slip.get_date_details()
            
        salary_slip.get_working_days_details()
        salary_slip.calculate_net_pay()
        
        # Restore the original method
        salary_slip.eval_condition_and_formula = original_eval_method
        
        # Clean up the temporary attribute
        if hasattr(salary_slip, '_manual_earnings_override'):
            delattr(salary_slip, '_manual_earnings_override')

        # Save the changes
        salary_slip.save()

        return {
            "status": "success",
            "message": "All salary components recalculated successfully with manual earnings",
            "gross_pay": salary_slip.gross_pay,
            "total_deduction": salary_slip.total_deduction,
            "net_pay": salary_slip.net_pay,
            "total_earnings": getattr(salary_slip, 'total_earnings', 0),
            "ctc": getattr(salary_slip, 'ctc', 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in recalculate_all_deductions: {str(e)}")
        frappe.throw(f"Error: {str(e)}")
