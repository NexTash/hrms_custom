import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class SalarySlipCustom(SalarySlip):
    @frappe.whitelist()
    def regenerate_salary_slip(self, save_after_regeneration=True):
        """
        Regenerate salary slip by clearing earnings and deductions
        and recalculating from scratch based on current salary structure
        """
        self.earnings = []
        self.deductions = []
        self.calculate_net_pay()
        
        # Only save if explicitly requested
        if save_after_regeneration:
            self.save()
    
    def recalculate_dependent_components(self):
        """
        Recalculate dependent components and update the document state
        without saving. This is used by hooks to avoid save recursion.
        """
        
        # First ensure all earnings have the correct flags from their salary component masters
        for earning in self.earnings:
            if earning.salary_component:
                component_data = frappe.get_cached_value("Salary Component", earning.salary_component, [
                    "deduct_full_tax_on_selected_payroll_date", "is_tax_applicable", "is_flexible_benefit"
                ])
                if component_data:
                    # Only set the flag if it's actually enabled in the component master
                    earning.deduct_full_tax_on_selected_payroll_date = component_data[0] or 0
                    earning.is_tax_applicable = component_data[1] or 0
                    earning.is_flexible_benefit = component_data[2] or 0
                    
                    # IMPORTANT: For components with full tax flag, set the additional_amount correctly
                    if component_data[0] and earning.amount:  # deduct_full_tax_on_selected_payroll_date is enabled
                        # Check if this is truly an additional salary (not from salary structure)
                        if not earning.get('default_amount') or earning.get('default_amount') == 0:
                            earning.additional_amount = earning.amount
                            earning.default_amount = 0
                        else:
                            # This is from salary structure, so it's not additional
                            earning.additional_amount = 0
        
        # Store current earnings before recalculation
        original_earnings = []
        for earning in self.earnings:
            original_earnings.append({
                'salary_component': earning.salary_component,
                'amount': earning.amount,
                'default_amount': earning.default_amount,
                'additional_amount': earning.additional_amount,
                'tax_on_additional_salary': earning.tax_on_additional_salary,
                'depends_on_payment_days': earning.depends_on_payment_days,
                'do_not_include_in_total': earning.do_not_include_in_total,
                'deduct_full_tax_on_selected_payroll_date': getattr(earning, 'deduct_full_tax_on_selected_payroll_date', 0),
                'is_tax_applicable': getattr(earning, 'is_tax_applicable', 1),
                'is_flexible_benefit': getattr(earning, 'is_flexible_benefit', 0)
            })
        
        # Instead of clearing everything, let's try a more targeted approach
        # Only recalculate deductions while preserving earnings
        
        # Calculate deductions with the current earnings intact
        if self.salary_structure:
            # First recalculate component amounts for deductions
            self.calculate_component_amounts("deductions")
            
            # Now we need to recalculate tax-based deductions that depend on taxable earnings
            # This includes income tax which needs to handle the full tax logic
            try:
                if self.payroll_period:
                    # Get tax slab if not already set
                    if not hasattr(self, 'tax_slab') or not self.tax_slab:
                        self.tax_slab = self.get_income_tax_slabs()
                    
                    # Calculate taxable earnings for the year - this sets up all prerequisite fields
                    self.compute_taxable_earnings_for_year()
                    
                    # Check if we have any earnings with full tax deduction
                    full_tax_earnings = []
                    for earning in self.earnings:
                        if getattr(earning, 'deduct_full_tax_on_selected_payroll_date', 0):
                            full_tax_earnings.append({
                                'component': earning.salary_component,
                                'amount': earning.amount,
                                'additional_amount': getattr(earning, 'additional_amount', 0),
                                'default_amount': getattr(earning, 'default_amount', 0)
                            })
                    
                    # Now recalculate variable tax components (like income tax)
                    # This will properly handle the full tax on additional earnings
                    for deduction in self.deductions:
                        component_data = frappe.get_cached_value("Salary Component", deduction.salary_component, [
                            "variable_based_on_taxable_salary", "depends_on_payment_days", "formula"
                        ])
                        
                        if component_data and component_data[0]:  # variable_based_on_taxable_salary
                            try:
                                # This will recalculate the tax amount including full tax logic
                                tax_amount = self.calculate_variable_based_on_taxable_salary(deduction.salary_component)
                                
                                if tax_amount is not None:
                                    deduction.amount = tax_amount
                                    
                            except Exception as e:
                                frappe.logger().error(f"Error recalculating {deduction.salary_component}: {str(e)}")
                
            except Exception as e:
                frappe.logger().error(f"Error in tax recalculation: {str(e)}")
        
        # Calculate net pay with updated deductions
        self.calculate_net_pay(skip_tax_breakup_computation=True)
        
        # Now calculate the income tax breakup
        try:
            self.compute_income_tax_breakup()
            
        except Exception as e:
            frappe.logger().error(f"Error recalculating income tax breakup for {self.name}: {str(e)}")
        
        # Update the document's modified timestamp and other metadata
        self.modified = frappe.utils.now()
        self.modified_by = frappe.session.user
