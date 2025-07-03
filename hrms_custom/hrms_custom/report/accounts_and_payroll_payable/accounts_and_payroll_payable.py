# Copyright (c) 2025, Gaston Vedani and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import qb
from frappe.query_builder import Criterion
from frappe.utils import cint, flt, getdate
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
    args = {
        "account_type": "Payable",
        "naming_by": ["Buying Settings", "supp_master_name"],
    }
    return AccountsAndPayrollPayableReport(filters).run(args)


class AccountsAndPayrollPayableReport(ReceivablePayableReport):
    def __init__(self, filters=None):
        super().__init__(filters)
        self.include_payroll_payable = cint(filters.get("include_payroll_payable"))

    def get_data(self):
        # Get the original data from parent class
        super().get_data()
        
        # If payroll payable is included, add payroll entries
        if self.include_payroll_payable:
            payroll_data = self.get_payroll_entries()
            if payroll_data:
                # Insert payroll data with proper spacing for grouping
                if not hasattr(self, 'data') or self.data is None:
                    self.data = []
                
                self.insert_payroll_entries(payroll_data)

    def insert_payroll_entries(self, payroll_data):
        """Insert payroll entries with proper spacing for grouping"""
        if not self.data:
            # If no existing data, just add payroll entries
            self.data.extend(payroll_data)
            if self.filters.get("group_by_party"):
                # Add subtotal row for payroll entries
                subtotal_row = self.create_payroll_subtotal_row(payroll_data)
                self.data.append(subtotal_row)
                # Add blank row after subtotal
                self.data.append(self.create_blank_row())
            return

        # Find where to insert (before any total rows)
        insert_index = len(self.data)
        for i, row in enumerate(self.data):
            # Look for total/summary rows and insert before them
            if isinstance(row, dict) and (
                row.get('party_name') == 'Total' or 
                row.get('party') == 'Total' or
                row.get('party', '').strip() == '' or  # Empty party indicates summary row
                'Total' in str(row.get('party_name', ''))
            ):
                insert_index = i
                break

        # If grouping is enabled, add proper spacing
        if self.filters.get("group_by_party"):
            # Add blank row before payroll entries (if there's existing data)
            if insert_index > 0:
                self.data.insert(insert_index, self.create_blank_row())
                insert_index += 1

            # Insert payroll entries excluding zero outstanding
            non_zero_payroll_data = [entry for entry in payroll_data if flt(entry["outstanding"]) != 0]
            for entry in non_zero_payroll_data:
                self.data.insert(insert_index, entry)
                insert_index += 1

            # Add subtotal row for payroll entries
            subtotal_row = self.create_payroll_subtotal_row(non_zero_payroll_data)
            self.data.insert(insert_index, subtotal_row)
            insert_index += 1

            # Only add blank row after subtotal if there are more rows after insert_index
            if insert_index < len(self.data):
                self.data.insert(insert_index, self.create_blank_row())
        else:
            # No grouping - just insert the entries
            for entry in payroll_data:
                self.data.insert(insert_index, entry)
                insert_index += 1

    def create_blank_row(self):
        """Create a blank row for spacing in grouped reports"""
        return {
            "posting_date": "",
            "party_type": "",
            "party": "",
            "party_name": "",
            "party_account": "",
            "cost_center": "",
            "voucher_type": "",
            "voucher_no": "",
            "due_date": "",
            "bill_no": "",
            "bill_date": "",
            "invoiced": "",
            "paid": "",
            "credit_note": "",
            "outstanding": "",
            "age": "",
            "range1": "",
            "range2": "",
            "range3": "",
            "range4": "",
            "range5": "",
            "currency": "",
            "supplier_group": ""
        }

    def create_payroll_subtotal_row(self, payroll_data):
        """Create a subtotal row for all payroll entries"""
        # Calculate totals from all payroll entries
        totals = {
            "invoiced": 0.0,
            "paid": 0.0,
            "credit_note": 0.0,
            "outstanding": 0.0,
            "range1": 0.0,
            "range2": 0.0,
            "range3": 0.0,
            "range4": 0.0,
            "range5": 0.0
        }
        
        currency = ""
        for entry in payroll_data:
            for field in totals:
                totals[field] += flt(entry.get(field, 0))
            if not currency and entry.get("currency"):
                currency = entry["currency"]

        return {
            "posting_date": "",
            "party_type": "",
            "party": "<b>Payroll Entries</b>",
            "party_name": "<b>Payroll Entries</b>",
            "party_account": "",
            "cost_center": "",
            "voucher_type": "",
            "voucher_no": "",
            "due_date": "",
            "bill_no": "",
            "bill_date": "",
            "invoiced": f"<b>{totals['invoiced']:.2f}</b>",
            "paid": f"<b>{totals['paid']:.2f}</b>",
            "credit_note": f"<b>{totals['credit_note']:.2f}</b>",
            "outstanding": f"<b>{totals['outstanding']:.2f}</b>",
            "age": "",
            "range1": f"<b>{totals['range1']:.2f}</b>" if totals['range1'] else "",
            "range2": f"<b>{totals['range2']:.2f}</b>" if totals['range2'] else "",
            "range3": f"<b>{totals['range3']:.2f}</b>" if totals['range3'] else "",
            "range4": f"<b>{totals['range4']:.2f}</b>" if totals['range4'] else "",
            "range5": f"<b>{totals['range5']:.2f}</b>" if totals['range5'] else "",
            "currency": currency,
            "supplier_group": ""
        }

    def create_subtotal_row(self, entry):
        """Create a subtotal row for the payroll entry"""
        return {
            "posting_date": "",
            "party_type": "",
            "party": "",
            "party_name": f"<b>{entry['party']}</b>",  # Bold party name
            "party_account": "",
            "cost_center": "",
            "voucher_type": "",
            "voucher_no": "",
            "due_date": "",
            "bill_no": "",
            "bill_date": "",
            "invoiced": f"<b>{entry['invoiced']}</b>",
            "paid": f"<b>{entry['paid']}</b>",
            "credit_note": f"<b>{entry['credit_note']}</b>",
            "outstanding": f"<b>{entry['outstanding']}</b>",
            "age": "",
            "range1": f"<b>{entry['range1']}</b>" if entry['range1'] else "",
            "range2": f"<b>{entry['range2']}</b>" if entry['range2'] else "",
            "range3": f"<b>{entry['range3']}</b>" if entry['range3'] else "",
            "range4": f"<b>{entry['range4']}</b>" if entry['range4'] else "",
            "range5": f"<b>{entry['range5']}</b>" if entry['range5'] else "",
            "currency": entry['currency'],
            "supplier_group": ""
        }

    def get_payroll_entries(self):
        """Get GL Entry ledgers for Payroll Entries using against_voucher_type"""
        
        # Query GL entries for payroll entries - include cost_center
        sql_query = """
            SELECT 
                voucher_no,
                against_voucher as party,
                'Payroll Entry' as party_type,
                against_voucher as party_name,
                posting_date,
                posting_date as due_date,
                account,
                cost_center,
                debit,
                credit,
                company,
                voucher_type,
                against_voucher_type as reference_type,
                against_voucher as reference_name
            FROM `tabGL Entry`
            WHERE against_voucher_type = 'Payroll Entry'
                AND posting_date <= %(report_date)s
                AND is_cancelled = 0
        """
        
        params = {"report_date": self.filters.report_date}
        
        if self.filters.get("company"):
            sql_query += " AND company = %(company)s"
            params["company"] = self.filters.company
            
        sql_query += " ORDER BY against_voucher, posting_date"

        gl_entries = frappe.db.sql(sql_query, params, as_dict=True)
        
        if not gl_entries:
            return []

        # Group by against_voucher to calculate net amounts
        payroll_summary = {}
        
        for entry in gl_entries:
            # Skip entries without an against_voucher
            if not entry.party:
                continue
                
            key = entry.party
            
            if key not in payroll_summary:
                payroll_summary[key] = {
                    "posting_date": entry.posting_date,
                    "party_type": "Payroll Entry",
                    "party": entry.party,
                    "party_name": entry.party,
                    "party_account": entry.account,      # Set the account name
                    "cost_center": entry.cost_center,      # Set the cost center
                    "voucher_type": "Payroll Entry", 
                    "voucher_no": entry.party,
                    "due_date": entry.posting_date,
                    "bill_no": "",
                    "bill_date": entry.posting_date,
                    "invoiced": 0.0,      
                    "paid": 0.0,          
                    "credit_note": 0.0,   
                    "outstanding": 0.0,   
                    "age": 0,
                    "range1": 0.0,
                    "range2": 0.0,
                    "range3": 0.0,
                    "range4": 0.0,
                    "range5": 0.0,
                    "currency": frappe.get_cached_value("Company", entry.company, "default_currency"),
                    "supplier_group": "Payroll"
                }
            else:
                # If we have multiple GL entries for the same payroll entry,
                # keep the account and cost center from the first payable account entry
                if not payroll_summary[key]["party_account"] and entry.account:
                    payroll_summary[key]["party_account"] = entry.account
                if not payroll_summary[key]["cost_center"] and entry.cost_center:
                    payroll_summary[key]["cost_center"] = entry.cost_center
            
            # For PAYABLE reports: Credits = what we OWE (invoiced), Debits = what we PAID
            if flt(entry.credit) > 0:
                payroll_summary[key]["invoiced"] += flt(entry.credit)
            
            if flt(entry.debit) > 0:
                payroll_summary[key]["paid"] += flt(entry.debit)

        # Calculate outstanding amounts and age buckets
        result = []
        for key, summary in payroll_summary.items():
            outstanding = flt(summary["invoiced"]) - flt(summary["paid"])
            
            # Include only entries with outstanding amounts
            if abs(outstanding) > 0.01:  # Small tolerance for rounding
                summary["outstanding"] = outstanding
                
                # Calculate age
                if summary["due_date"]:
                    age = (getdate(self.filters.report_date) - getdate(summary["due_date"])).days
                    summary["age"] = max(age, 0)
                    
                    # Set age buckets based on the report's range settings
                    self.set_age_bucket(summary, age, outstanding)
                
                result.append(summary)
        
        return result
        
    def set_age_bucket(self, summary, age, outstanding):
        """Set the appropriate age bucket for the outstanding amount"""
        # Get range settings from filters (default: 30, 60, 90, 120)
        ranges = [int(x.strip()) for x in self.filters.get("range", "30, 60, 90, 120").split(",")]
        
        if age <= ranges[0]:  # 0-30
            summary["range1"] = outstanding
        elif age <= ranges[1]:  # 31-60
            summary["range2"] = outstanding
        elif age <= ranges[2]:  # 61-90
            summary["range3"] = outstanding
        elif age <= ranges[3]:  # 91-120
            summary["range4"] = outstanding
        else:  # 121+
            summary["range5"] = outstanding

    def run(self, args):
        """Override run method to update totals after adding payroll data"""
        columns, data, message, chart, report_summary, skip_total_row = super().run(args)
        
        # Update the grand total row to include payroll amounts
        if self.include_payroll_payable and data:
            self.update_grand_total(data)
        
        return columns, data, message, chart, report_summary, skip_total_row
    
    def update_grand_total(self, data):
        """Update the grand total row to include payroll amounts"""
        payroll_totals = {
            "invoiced": 0.0,
            "paid": 0.0,
            "outstanding": 0.0,
            "range1": 0.0,
            "range2": 0.0,
            "range3": 0.0,
            "range4": 0.0,
            "range5": 0.0
        }
        
        # Find payroll entries and sum their amounts
        for row in data:
            if isinstance(row, dict) and row.get("party_type") == "Payroll Entry":
                for field in payroll_totals:
                    payroll_totals[field] += flt(row.get(field, 0))
        
        # Find and update the Total row
        for i, row in enumerate(data):
            if isinstance(row, dict) and (
                row.get('party_name') == 'Total' or 
                row.get('party') == 'Total' or
                'Total' in str(row.get('party_name', ''))
            ):
                # Update the total row with payroll amounts
                for field in payroll_totals:
                    if field in row:
                        current_value = flt(str(row[field]).replace('<b>', '').replace('</b>', ''))
                        new_value = current_value + payroll_totals[field]
                        row[field] = f"<b>{new_value}</b>" if '<b>' in str(row[field]) else new_value
                break
