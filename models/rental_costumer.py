# rental_customer.py - COMPLETE VERSION
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class RentalCustomer(models.Model):
    _name = "rental.customer"
    _description = "Rental Customer"
    _rec_name = "name"
    _order = "name"
    
    # Basic Information (yang sudah ada di kode lama Anda)
    name = fields.Char(string="Customer Name", required=True, index=True)
    email = fields.Char(string="Email", required=True, index=True)
    phone = fields.Char(string="Phone", required=True)
    
    # Additional Professional Fields (TAMBAHAN BARU)
    customer_code = fields.Char(string="Customer Code", readonly=True, copy=False)
    address = fields.Text(string="Address")
    city = fields.Char(string="City")
    state = fields.Char(string="State")
    zip_code = fields.Char(string="ZIP Code")
    country = fields.Char(string="Country")  # Simple text field, no dependency
    
    # Business Fields (TAMBAHAN BARU)
    customer_type = fields.Selection([
        ('individual', 'Individual'),
        ('company', 'Company')
    ], string="Customer Type", default='individual', required=True)
    
    company_name = fields.Char(string="Company Name")
    tax_id = fields.Char(string="Tax ID")
    
    # Status and Activity (TAMBAHAN BARU)
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")
    
    # Credit and Financial (TAMBAHAN BARU)
    credit_limit = fields.Float(string="Credit Limit", default=0.0)
    
    # Relationship with orders (TAMBAHAN BARU)
    rental_order_ids = fields.One2many('rental.order', 'customer_id', string="Rental Orders")
    rental_count = fields.Integer(string="Total Rentals", compute="_compute_rental_stats", store=True)
    
    # Computed Fields (TAMBAHAN BARU)
    total_spent = fields.Float(string="Total Spent", compute="_compute_rental_stats")
    last_rental_date = fields.Date(string="Last Rental", compute="_compute_rental_stats")
    
    # Customer Rating (TAMBAHAN BARU)
    rating = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent')
    ], string="Customer Rating", default='3')
    
    @api.model
    def create(self, vals):
        """Generate customer code when creating new customer"""
        if not vals.get('customer_code'):
            vals['customer_code'] = self.env['ir.sequence'].next_by_code('rental.customer.code') or 'CUST0001'
        return super(RentalCustomer, self).create(vals)
    
    @api.depends('rental_order_ids')
    def _compute_rental_stats(self):
        """Compute rental statistics"""
        for customer in self:
            orders = customer.rental_order_ids.filtered(lambda o: o.state in ['confirmed', 'done'])
            customer.rental_count = len(orders)
            customer.total_spent = sum(orders.mapped('total_price'))
            
            if orders:
                customer.last_rental_date = max(orders.mapped('start_date') or [False])
            else:
                customer.last_rental_date = False
    
    @api.constrains('email')
    def _check_email_format(self):
        """Validate email format"""
        for customer in self:
            if customer.email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, customer.email):
                    raise ValidationError("Invalid email format!")
    
    @api.constrains('phone')
    def _check_phone_format(self):
        """Basic phone validation"""
        for customer in self:
            if customer.phone:
                # Remove spaces and special characters for validation
                phone_clean = re.sub(r'[\s\-\(\)]', '', customer.phone)
                if not phone_clean.isdigit() or len(phone_clean) < 8:
                    raise ValidationError("Phone number must contain at least 8 digits!")
    
    @api.constrains('credit_limit')
    def _check_credit_limit(self):
        """Validate credit limit"""
        for customer in self:
            if customer.credit_limit < 0:
                raise ValidationError("Credit limit cannot be negative!")
    
    def action_view_rental_orders(self):
        """Action to view customer's rental orders"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Rental Orders',
            'res_model': 'rental.order',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }
    
    def name_get(self):
        """Custom display name"""
        result = []
        for customer in self:
            name = customer.name
            if customer.customer_code:
                name = f"[{customer.customer_code}] {name}"
            result.append((customer.id, name))
        return result