from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RentalPaymentWizard(models.TransientModel):
    _name = 'rental.payment.wizard'
    _description = 'Rental Payment Wizard'
    
    order_id = fields.Many2one('rental.order', string='Rental Order', required=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today, required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
    ], string='Payment Method', required=True, default='cash')
    notes = fields.Text(string='Notes')
    
    # Untuk display info
    current_paid = fields.Float(string='Current Paid Amount', related='order_id.paid_amount', readonly=True)
    total_amount = fields.Float(string='Total Amount', related='order_id.total_price', readonly=True)
    remaining = fields.Float(string='Remaining Amount', related='order_id.remaining_amount', readonly=True)
    
    @api.constrains('payment_amount')
    def _check_payment_amount(self):
        for wizard in self:
            if wizard.payment_amount <= 0:
                raise ValidationError("Payment amount must be greater than 0!")
            if wizard.payment_amount > wizard.remaining:
                raise ValidationError(f"Payment amount cannot exceed remaining amount: {wizard.remaining}!")
    
    def action_confirm_payment(self):
        """Process the payment"""
        self.ensure_one()
        
        # Update paid amount di order
        self.order_id.paid_amount += self.payment_amount
        
        # Update payment status
        if self.order_id.paid_amount >= self.order_id.total_price:
            self.order_id.payment_status = 'paid'
        elif self.order_id.paid_amount > 0:
            self.order_id.payment_status = 'partial'
        
        # TODO: Nanti bisa ditambahkan create payment record/journal entry
        
        return {'type': 'ir.actions.act_window_close'}