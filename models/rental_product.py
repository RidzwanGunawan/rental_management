# rental_product.py - COMPLETE VERSION
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class RentalProduct(models.Model):
    _name = 'rental.product'
    _description = 'Rental Product'
    _rec_name = "name"
    _order = "name"
    
    # Basic Information (yang sudah ada di kode lama Anda)
    name = fields.Char(string="Product Name", required=True, index=True)
    description = fields.Text(string="Description")  # Ubah dari Text ke Html kalau mau rich text
    price_per_day = fields.Float(string="Price per day", required=True)
    status = fields.Selection([
        ("available", "Available"),
        ("rented", "Rented"),
        ("maintenance", "Under Maintenance"),  # TAMBAHAN BARU
        ("damaged", "Damaged"),               # TAMBAHAN BARU
        ("retired", "Retired")                # TAMBAHAN BARU
    ], string="Status", default="available")
    
    # Additional Professional Fields (TAMBAHAN BARU)
    product_code = fields.Char(string="Product Code", readonly=True, copy=False)
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    serial_number = fields.Char(string="Serial Number", copy=False)
    
    # Pricing Information (TAMBAHAN BARU)
    price_per_week = fields.Float(string="Price per Week", compute="_compute_weekly_price", store=True)
    price_per_month = fields.Float(string="Price per Month", compute="_compute_monthly_price", store=True)
    weekend_price = fields.Float(string="Weekend Price per Day", default=0.0)
    holiday_price = fields.Float(string="Holiday Price per Day", default=0.0)
    
    # Deposit and Insurance (TAMBAHAN BARU)
    security_deposit = fields.Float(string="Security Deposit Required", default=0.0)
    insurance_required = fields.Boolean(string="Insurance Required", default=False)
    insurance_cost_per_day = fields.Float(string="Insurance Cost per Day", default=0.0)
    
    # Physical Attributes (TAMBAHAN BARU)
    weight = fields.Float(string="Weight (kg)")
    dimensions = fields.Char(string="Dimensions (L x W x H)")
    color = fields.Char(string="Color")
    year_manufactured = fields.Integer(string="Year of Manufacture")
    
    # Status and Availability (TAMBAHAN BARU)
    active = fields.Boolean(string="Active", default=True)
    
    # Location and Storage (TAMBAHAN BARU)
    location = fields.Char(string="Storage Location")
    
    # Condition (TAMBAHAN BARU)
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string="Condition", default='excellent')
    
    # Maintenance (TAMBAHAN BARU)
    last_maintenance_date = fields.Date(string="Last Maintenance Date")
    next_maintenance_date = fields.Date(string="Next Maintenance Date")
    maintenance_interval_days = fields.Integer(string="Maintenance Interval (Days)", default=365)
    
    # Purchase Information (TAMBAHAN BARU)
    purchase_date = fields.Date(string="Purchase Date")
    purchase_price = fields.Float(string="Purchase Price")
    supplier = fields.Char(string="Supplier")  # Simple text field
    warranty_expiry = fields.Date(string="Warranty Expiry")
    
    # Rental History and Statistics (TAMBAHAN BARU)
    rental_order_ids = fields.One2many('rental.order', 'product_id', string="Rental Orders")
    rental_count = fields.Integer(string="Total Rentals", compute="_compute_rental_stats")
    total_rental_days = fields.Integer(string="Total Rental Days", compute="_compute_rental_stats")
    total_revenue = fields.Float(string="Total Revenue", compute="_compute_rental_stats")
    utilization_rate = fields.Float(string="Utilization Rate (%)", compute="_compute_utilization_rate")
    
    # Availability and Booking (TAMBAHAN BARU)
    min_rental_days = fields.Integer(string="Minimum Rental Days", default=1)
    max_rental_days = fields.Integer(string="Maximum Rental Days", default=365)
    advance_booking_days = fields.Integer(string="Advance Booking Required (Days)", default=0)
    
    # Special Instructions (TAMBAHAN BARU)
    setup_instructions = fields.Text(string="Setup Instructions")
    safety_instructions = fields.Text(string="Safety Instructions")
    return_instructions = fields.Text(string="Return Instructions")
    
    # Internal notes (TAMBAHAN BARU)
    internal_notes = fields.Text(string="Internal Notes")
    
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    
    @api.model
    def create(self, vals):
        """Generate product code when creating new product"""
        if not vals.get('product_code'):
            # Simple sequence - nanti bisa diganti dengan ir.sequence
            last_product = self.search([], order='id desc', limit=1)
            if last_product and last_product.product_code:
                last_number = int(last_product.product_code.replace('PROD', '') or '0')
                vals['product_code'] = f'PROD{str(last_number + 1).zfill(4)}'
            else:
                vals['product_code'] = 'PROD0001'
        return super(RentalProduct, self).create(vals)
    
    @api.depends('price_per_day')
    def _compute_weekly_price(self):
        """Compute weekly price with discount"""
        for product in self:
            product.price_per_week = product.price_per_day * 7 * 0.85  # 15% discount for weekly
    
    @api.depends('price_per_day')
    def _compute_monthly_price(self):
        """Compute monthly price with discount"""
        for product in self:
            product.price_per_month = product.price_per_day * 30 * 0.75  # 25% discount for monthly
    
    @api.depends('rental_order_ids')
    def _compute_rental_stats(self):
        """Compute rental statistics"""
        for product in self:
            completed_orders = product.rental_order_ids.filtered(lambda o: o.state == 'done')
            product.rental_count = len(completed_orders)
            
            # Compute total rental days
            total_days = 0
            for order in completed_orders:
                if order.start_date and order.end_date:
                    days = (order.end_date - order.start_date).days + 1
                    total_days += days
            product.total_rental_days = total_days
            
            # Compute total revenue
            product.total_revenue = sum(completed_orders.mapped('total_price'))
    
    @api.depends('total_rental_days', 'purchase_date')
    def _compute_utilization_rate(self):
        """Compute utilization rate"""
        for product in self:
            if product.purchase_date:
                days_owned = (fields.Date.today() - product.purchase_date).days
                if days_owned > 0:
                    product.utilization_rate = (product.total_rental_days / days_owned) * 100
                else:
                    product.utilization_rate = 0
            else:
                product.utilization_rate = 0
    
    @api.constrains('price_per_day', 'security_deposit')
    def _check_pricing(self):
        """Validate pricing"""
        for product in self:
            if product.price_per_day <= 0:
                raise ValidationError("Price per day must be greater than 0!")
            if product.security_deposit < 0:
                raise ValidationError("Security deposit cannot be negative!")
    
    @api.constrains('min_rental_days', 'max_rental_days')
    def _check_rental_days_limits(self):
        """Validate rental days limits"""
        for product in self:
            if product.min_rental_days <= 0:
                raise ValidationError("Minimum rental days must be at least 1!")
            if product.max_rental_days < product.min_rental_days:
                raise ValidationError("Maximum rental days must be greater than minimum rental days!")
    
    @api.onchange('last_maintenance_date', 'maintenance_interval_days')
    def _onchange_maintenance_schedule(self):
        """Auto-calculate next maintenance date"""
        if self.last_maintenance_date and self.maintenance_interval_days:
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_interval_days)
    
    def action_set_maintenance(self):
        """Set product to maintenance status"""
        for product in self:
            if product.status == 'rented':
                raise ValidationError("Cannot set rented product to maintenance!")
            product.status = 'maintenance'
    
    def action_set_available(self):
        """Set product back to available"""
        for product in self:
            product.status = 'available'
    
    def action_view_rental_history(self):
        """View rental history for this product"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Rental History',
            'res_model': 'rental.order',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }
    
    def check_availability(self, start_date, end_date):
        """Check if product is available for given period"""
        conflicting_orders = self.rental_order_ids.filtered(
            lambda o: o.state in ['confirmed', 'ongoing'] and not (
                o.end_date < start_date or o.start_date > end_date
            )
        )
        return len(conflicting_orders) == 0
    
    def name_get(self):
        """Custom display name"""
        result = []
        for product in self:
            name = product.name
            if product.product_code:
                name = f"[{product.product_code}] {name}"
            if product.status != 'available':
                name = f"{name} ({product.status.title()})"
            result.append((product.id, name))
        return result