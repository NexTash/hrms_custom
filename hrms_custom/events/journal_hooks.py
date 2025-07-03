import frappe

def process_salary_payment(doc, method):
    """Update salary slip custom fields when journal entry is submitted"""
    payroll_entries = [
        d for d in doc.accounts
        if d.reference_type == "Payroll Entry" and d.debit > 0
    ]
    if not payroll_entries:
        return
    ref_names = {d.reference_name for d in payroll_entries}
    if len(ref_names) != 1:
        return

    payroll_entry = list(ref_names)[0]
    salary_slips = frappe.get_all("Salary Slip", 
        filters={"payroll_entry": payroll_entry}, 
        fields=["name", "employee", "net_pay", "custom_journal_amount"]
    )

    for row in payroll_entries:
        for slip in salary_slips:
            if row.party == slip.employee:
                slip_doc = frappe.get_doc("Salary Slip", slip.name)
                # Convert to float to handle both string and numeric values
                existing_paid = float(slip_doc.custom_journal_amount or 0)
                total_paid = existing_paid + float(row.debit)
                if total_paid >= slip_doc.net_pay:
                    status = "Paid"
                elif total_paid > 0:
                    status = "Partially Paid"
                else:
                    status = "Unpaid"
                slip_doc.db_set("custom_journal_amount", total_paid)
                slip_doc.db_set("payment_status", status)
                slip_doc.save()
    frappe.db.commit()

def reverse_salary_payment(doc, method):
    """Revert salary slip custom fields when journal entry is cancelled"""
    payroll_entries = [
        d for d in doc.accounts
        if d.reference_type == "Payroll Entry" and d.debit > 0
    ]
    if not payroll_entries:
        return
    ref_names = {d.reference_name for d in payroll_entries}
    if len(ref_names) != 1:
        return

    payroll_entry = list(ref_names)[0]
    salary_slips = frappe.get_all("Salary Slip", 
        filters={"payroll_entry": payroll_entry}, 
        fields=["name", "employee", "net_pay", "custom_journal_amount"]
    )

    for row in payroll_entries:
        for slip in salary_slips:
            if row.party == slip.employee:
                slip_doc = frappe.get_doc("Salary Slip", slip.name)
                # Convert to float to handle both string and numeric values
                existing_paid = float(slip_doc.custom_journal_amount or 0)
                # Subtract the amount that was previously added
                total_paid = existing_paid - float(row.debit)
                # Ensure it doesn't go below zero
                total_paid = max(0, total_paid)
                
                if total_paid >= slip_doc.net_pay:
                    status = "Paid"
                elif total_paid > 0:
                    status = "Partially Paid"
                else:
                    status = "Unpaid"
                slip_doc.db_set("custom_journal_amount", total_paid)
                slip_doc.db_set("payment_status", status)
                slip_doc.save()
    frappe.db.commit()
