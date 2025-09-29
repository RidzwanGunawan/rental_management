# rental_order.py - COMPLETE VERSION
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class RentalOrder(models.Model):
    _name = "rental.order"
    _description = "Rental Order"
    _rec_name = "name"
    _order = "create_date desc"
    
    # Basic Information (YANG SUDAH ADA + TAMBAHAN)
    name = fields.Char(string="Order Number", readonly=True, copy=False, default='New')
    customer_id = fields.Many2one("rental.customer", string="Customer", required=True)
    product_id = fields.Many2one("rental.product", string="Product", required=True)
    
    # Date Management (YANG SUDAH ADA + PERBAIKAN)
    start_date = fields.Date(string="Start Date", required=True)  # Tetap Date, bukan Datetime
    end_date = fields.Date(string="End Date", required=True)      # Tetap Date, bukan Datetime
    actual_return_date = fields.Date(string="Actual Return Date")  # TAMBAHAN BARU
    
    # Pricing (YANG SUDAH ADA + TAMBAHAN)
    price_per_day = fields.Float(string="Price per Day", related='product_id.price_per_day', store=True)
    rental_days = fields.Integer(string="Rental Days", compute="_compute_rental_days", store=True)
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    tax_amount = fields.Float(string="Tax Amount", compute="_compute_tax_amount", store=True)
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)
    
    # Additional Charges (TAMBAHAN BARU)
    deposit_amount = fields.Float(string="Security Deposit", related='product_id.security_deposit', store=True)
    late_fee = fields.Float(string="Late Fee", compute="_compute_late_fee", store=True)
    damage_fee = fields.Float(string="Damage Fee", default=0.0)
    insurance_fee = fields.Float(string="Insurance Fee", compute="_compute_insurance_fee", store=True)
    
    # Workflow and Status (YANG SUDAH ADA + TAMBAHAN)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),        # TAMBAHAN BARU
        ('returned', 'Returned'),      # TAMBAHAN BARU  
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft')
    
    # Additional Information (TAMBAHAN BARU)
    notes = fields.Text(string="Customer Notes")
    internal_notes = fields.Text(string="Internal Notes")
    return_condition = fields.Text(string="Return Condition Notes")
    
    # System Fields (TAMBAHAN BARU)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    
    # Payment Status (TAMBAHAN BARU)
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded')
    ], string="Payment Status", default='unpaid')
    
    paid_amount = fields.Float(string="Paid Amount", default=0.0)
    remaining_amount = fields.Float(string="Remaining Amount", compute="_compute_remaining_amount", store=True)
    
    @api.model
    def create(self, vals):
        """Generate sequence number for new rental order"""
        if vals.get('name', 'New') == 'New':
            # Simple sequence - nanti bisa diganti dengan ir.sequence
            last_order = self.search([], order='id desc', limit=1)
            if last_order and last_order.name != 'New':
                last_number = int(last_order.name.replace('RO', '') or '0')
                vals['name'] = f'RO{str(last_number + 1).zfill(4)}'
            else:
                vals['name'] = 'RO0001'
        return super(RentalOrder, self).create(vals)
    
    @api.depends('start_date', 'end_date')
    def _compute_rental_days(self):
        """Compute rental days"""
        for order in self:
            if order.start_date and order.end_date:
                delta = order.end_date - order.start_date
                order.rental_days = delta.days + 1 if delta.days >= 0 else 0
            else:
                order.rental_days = 0
    
    @api.depends('rental_days', 'price_per_day')
    def _compute_subtotal(self):
        """Compute subtotal"""
        for order in self:
            order.subtotal = order.rental_days * order.price_per_day
    
    @api.depends('subtotal')
    def _compute_tax_amount(self):
        """Compute tax (example: 10% tax rate)"""
        for order in self:
            tax_rate = 0.10  # 10% tax - bisa dibuat configurable nanti
            order.tax_amount = order.subtotal * tax_rate
    
    @api.depends('rental_days', 'product_id.insurance_required', 'product_id.insurance_cost_per_day')
    def _compute_insurance_fee(self):
        """Compute insurance fee if required"""
        for order in self:
            if order.product_id.insurance_required:
                order.insurance_fee = order.rental_days * order.product_id.insurance_cost_per_day
            else:
                order.insurance_fee = 0.0
    
    @api.depends('subtotal', 'tax_amount', 'late_fee', 'damage_fee', 'insurance_fee')
    def _compute_total_price(self):
        """Compute total price"""
        for order in self:
            order.total_price = (order.subtotal + order.tax_amount + 
                               order.late_fee + order.damage_fee + order.insurance_fee)
    
    @api.depends('total_price', 'paid_amount')
    def _compute_remaining_amount(self):
        """Compute remaining payment amount"""
        for order in self:
            order.remaining_amount = order.total_price - order.paid_amount
    
    @api.depends('end_date', 'actual_return_date', 'price_per_day')
    def _compute_late_fee(self):
        """Compute late fee if returned late"""
        for order in self:
            if (order.actual_return_date and order.end_date and 
                order.actual_return_date > order.end_date):
                late_days = (order.actual_return_date - order.end_date).days
                late_fee_per_day = order.price_per_day * 0.5  # 50% of daily rate as late fee
                order.late_fee = late_days * late_fee_per_day
            else:
                order.late_fee = 0
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate date logic"""
        for order in self:
            if order.start_date and order.end_date:
                if order.end_date <= order.start_date:
                    raise ValidationError("End date must be after start date!")
                
                # Check if start date is not in the past (except for draft state)
                if order.state != 'draft' and order.start_date < fields.Date.today():
                    raise ValidationError("Start date cannot be in the past for confirmed orders!")
    
    @api.constrains('product_id', 'start_date', 'end_date')
    def _check_product_availability(self):
        """Check if product is available for the rental period"""
        for order in self:
            if (order.product_id and order.start_date and order.end_date and 
                order.state not in ['cancelled', 'draft']):
                # Find overlapping rentals for the same product
                overlapping_orders = self.search([
                    ('product_id', '=', order.product_id.id),
                    ('id', '!=', order.id),
                    ('state', 'in', ['confirmed', 'ongoing']),
                    ('start_date', '<=', order.end_date),
                    ('end_date', '>=', order.start_date)
                ])
                if overlapping_orders:
                    raise ValidationError(f"Product '{order.product_id.name}' is not available for the selected period!")
    
    @api.constrains('paid_amount')
    def _check_paid_amount(self):
        """Validate paid amount"""
        for order in self:
            if order.paid_amount < 0:
                raise ValidationError("Paid amount cannot be negative!")
            if order.paid_amount > order.total_price:
                raise ValidationError("Paid amount cannot exceed total price!")
    
    @api.onchange('paid_amount', 'total_price')
    def _onchange_payment_status(self):
        """Auto-update payment status based on paid amount"""
        for order in self:
            if order.paid_amount == 0:
                order.payment_status = 'unpaid'
            elif order.paid_amount >= order.total_price:
                order.payment_status = 'paid'
            else:
                order.payment_status = 'partial'
    
    # ======== WORKFLOW ACTIONS ========
    
    def action_confirm(self):
        """Confirm the rental order"""
        for order in self:
            if order.state != 'draft':
                raise UserError("Only draft orders can be confirmed!")
            
            # Check product availability
            if not order.product_id.check_availability(order.start_date, order.end_date):
                raise UserError(f"Product '{order.product_id.name}' is not available for selected dates!")
            
            order.state = 'confirmed'
            order.product_id.status = 'rented'
    
    def action_start_rental(self):
        """Start the rental (when customer picks up)"""
        for order in self:
            if order.state != 'confirmed':
                raise UserError("Only confirmed orders can be started!")
            order.state = 'ongoing'
    
    def action_return(self):
        """Mark as returned (when customer returns the item)"""
        for order in self:
            if order.state != 'ongoing':
                raise UserError("Only ongoing rentals can be returned!")
            order.actual_return_date = fields.Date.today()
            order.state = 'returned'
    
    def action_done(self):
        """Mark as done (complete the rental process)"""
        for order in self:
            if order.state != 'returned':
                raise UserError("Only returned rentals can be marked as done!")
            order.state = 'done'
            order.product_id.status = 'available'
    
    def action_cancel(self):
        """Cancel the rental order"""
        for order in self:
            if order.state in ['done']:
                raise UserError("Cannot cancel completed rentals!")
            order.state = 'cancelled'
            if order.product_id.status == 'rented':
                order.product_id.status = 'available'
    
    def action_reset_to_draft(self):
        """Reset to draft state"""
        for order in self:
            if order.state not in ['cancelled']:
                raise UserError("Can only reset cancelled orders to draft!")
            order.state = 'draft'
            # Don't change product status here, let confirm action handle it
    
    def action_register_payment(self):
        """Open payment registration wizard"""
        # Ini bisa dikembangkan nanti untuk payment wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Register Payment',
            'res_model': 'rental.payment.wizard',  # Model yang bisa dibuat nanti
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
    
    def name_get(self):
        """Custom display name"""
        result = []
        for order in self:
            name = f"{order.name} - {order.customer_id.name}"
            if order.product_id:
                name = f"{name} ({order.product_id.name})"
            result.append((order.id, name))
        return result