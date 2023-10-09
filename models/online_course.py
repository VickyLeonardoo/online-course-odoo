from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class online_course(models.Model):
    _name = 'online.course'
    _inherit = 'mail.thread'
    application_no = fields.Char('Application No.', default='/')

    def func_to_app(self):
        if self.status == 'draft' and self.application_no == '/':
            self.status = 'application'
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'your.sequence.code')])
            sequence_pool = self.env['ir.sequence']
            application_no = sequence_pool.sudo().get_id(sequence_id.id)
            self.write({'application_no': application_no})

            #membuat res.partner

            partner_vals = {
                'name': self.name,
                'mobile': self.mobile,
                'dob': self.dob,
                'email': self.email,
                'gender': self.gender,
                'course_id': self.id
            }
            if not self.partner_id:
                partner = self.env['res.partner'].create(partner_vals)
                self.partner_id = partner.id
            else:
                self.partner_id.write(partner_vals)

    def func_to_conf(self):
        if self.status == 'application':
            self.status = 'confirm'
            payment_term_obj = self.env.ref('account.account_payment_term_net')
            invoice_vals = {
                'partner_id': self.partner_id.id,
                'date_invoice': datetime.today().date(),
                'payment_term_id': payment_term_obj.id,
                'date_due': (datetime.today().date() + relativedelta(days=payment_term_obj.line_ids[0].days)),
            }
            invoice = self.env['account.invoice'].create(invoice_vals)

            for line in self.order_line_ids:
                line.write({'invoice_id': invoice.id})
                invoice_line_vals = {
                    'product_id': line.event_id.product_id.id,
                    'name': line.event_id.product_id.name,
                    'quantity': 1,
                    'price_unit': line.event_id.product_id.list_price,
                    'invoice_id': invoice.id,
                    'account_id' : line.online_course_id.partner_id.id,
                }
                self.env['account.invoice.line'].create(invoice_line_vals)

                invoice.online_course_id = self
                

    def func_to_pay(self):
        if self.status == 'confirm':
            self.status = 'payment_receive'

        if self.invoice_ids:
            self.invoice_ids.action_invoice_open()

            for invoice in self.invoice_ids:
                if invoice.state == 'open':
                    payment = {
                        'amount': invoice.residual,
                        'journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
                        'payment_date': fields.Date.today(),
                        'communication': invoice.number,
                        'partner_id': invoice.partner_id.id,
                        'payment_type': 'inbound',
                        'partner_type': 'supplier',
                        'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                        'invoice_ids': [(4, invoice.id)],
                    }
                    payment_obj = self.env['account.payment'].create(payment)
                    payment_obj.post()

                    registration_vals = {
                    'event_id': self.order_line_ids.event_id.id,
                    'name': self.partner_id.name,
                    'phone': self.partner_id.phone,
                    'partner_id': self.partner_id.id,
                    'email': self.partner_id.email,
                    'state': 'draft',
                    'online_course_id': self.id,
                }
                    registration = self.env['event.registration'].create(registration_vals)
                    registration.action_confirm()

    def func_to_acc(self):
        if self.status == 'payment_receive':
            self.status = 'accepted'

    partner_id = fields.Many2one('res.partner', string="Partner Id")
    name = fields.Char(string="Name", required=True)
    dob = fields.Date(string="DOB", required=True)
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female')], required=True)
    email = fields.Char(string="Email", required=True)
    mobile = fields.Char(string="Mobile", required=True)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    status = fields.Selection(
    string='Status',
    selection=[('draft', 'Draft'),
               ('application', 'Application'),
               ('confirm', 'Confirm'),
               ('payment_receive', 'Payment Receive'),
               ('accepted', 'Accepted')],
    required=True,
    default = 'draft'
    )
    order_line_ids = fields.One2many('order.line', 'online_course_id', string='Order Lines')
    invoice_ids = fields.One2many('account.invoice', 'online_course_id', string="Invoice")
    registration_ids = fields.One2many('event.registration', 'online_course_id', string="Registrations")

    @api.model
    def create(self, vals):
        vals['user_id'] = self.env.user.id
        return super(online_course, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.mobile = self.partner_id.mobile
            self.application_date = self.partner_id.date
            self.dob = self.partner_id.dob
            self.email = self.partner_id.email
            self.gender = self.partner_id.gender
        else:
            self.name = False

    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                birth_date = fields.Date.from_string(record.dob)
                today_date = datetime.today().date()
                age = today_date.year - birth_date.year - ((today_date.month, today_date.day) < (birth_date.month, birth_date.day))
                record.age = age
            else:
                record.age = 0

    @api.multi
    def unlink(self):
        for course in self:
            if course.application_no:
                raise UserError('Cannot delete course with an application number.')
        return super(online_course, self).unlink()

    @api.model
    def write(self, vals):
        if 'order_line_ids' in vals and not vals['order_line_ids']:
            raise ValidationError("Order lines cannot be empty!")
        return super(online_course, self).write(vals)

    @api.model
    def create(self, vals):
        if 'order_line_ids' not in vals:
            raise ValidationError("Order lines cannot be empty!")
        return super(online_course, self).create(vals)
   
class online_partner(models.Model):
    _inherit = 'res.partner'

    dob = fields.Date(string='Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')

    @api.model
    def send_birthday_emails(self):
        today = datetime.today().date()
        partners = self.env['res.partner'].search([('dob', '!=', False)])
        for partner in partners:
            birth_date = fields.Date.from_string(partner.dob)
            if today.month == birth_date.month and today.day == birth_date.day:
                template = self.env.ref('online_course.birthday_email_template')
                template_ctx = {'object': partner}
                email_body = template.with_context(template_ctx).render_template(template.body_html, model='res.partner', res_ids=partner.ids)
                email_values = {
                    'subject': template.subject,
                    'body_html': email_body,
                    'email_to': partner.email,
                    'res_id': partner.id,
                    'model': 'res.partner',
                    'auto_delete': True,
                }
                mail = self.env['mail.mail'].create(email_values)
                mail.send()

class course_list(models.Model):
    _name = 'course.list'

    name = fields.Char(string="Name")

class EventEvent(models.Model):
    _inherit = 'event.event'

    online_course_id = fields.Many2one('online.course', string='Course')
    price_unit = fields.Float(string='Price Unit', store=True)
    product_id = fields.Many2one('product.product' , string="Product")
    email_to = fields.Char(string='To', required=True)
    email_subject = fields.Char(string='Subject', required=True)
    email_body = fields.Html(string='Body', required=True)

    def generate_event_attendees_report(self):
        report_url = '/online_course/event_attendees_report?event_id=%s' % self.id
        return {
            'type': 'ir.actions.act_url',
            'url': report_url,
            'target': 'new',
        }
    def generate_attendees_report_pdf(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/online_course/event_attendees_report_pdf?event_id={self.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': report_url,
            'target': 'new',
        }
    
class course_order_line(models.Model):
    _name = 'order.line'
    _description = 'Order Line'
    
    event_id = fields.Many2one('event.event', string='Event')
    online_course_id = fields.Many2one('online.course', string='Course')
    voucher_id = fields.Many2one('online.course.voucher', string='Voucher')
    price_unit = fields.Float(related='event_id.product_id.lst_price', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    @api.onchange('voucher_id')
    def _onchange_voucher_id(self):
        if self.voucher_id:
            if self.voucher_id.type == 'percentage':
                self.total_amount = self.price_unit * (100 - self.voucher_id.value) / 100
            elif self.voucher_id.type == 'amount':
                self.total_amount = self.price_unit - self.voucher_id.value
        else:
            self.total_amount = self.price_unit

    @api.depends('price_unit', 'voucher_id')
    def _compute_total_amount(self):
        for line in self:
            if line.voucher_id:
                if line.voucher_id.type == 'percentage':
                    line.total_amount = line.price_unit * (100 - line.voucher_id.value) / 100
                elif line.voucher_id.type == 'amount':
                    line.total_amount = line.price_unit - line.voucher_id.value
            else:
                line.total_amount = line.price_unit
    
class online_course_voucher(models.Model):
    _name = 'online.course.voucher'
    _description = 'Voucher'

    name = fields.Char(string='Name')
    type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], string='Type', required=True)
    value = fields.Float(string='Value', required=True)
    # order_line_id = fields.Many2one('order.line', string='Sale Order Line')
    

    @api.depends('price_unit', 'voucher_id', 'voucher_id.value', 'voucher_id.type')
    def _compute_total_amount(self):
     for record in self:
        if record.voucher_id:
            if record.voucher_id.type == 'percentage':
                record.total_amount = record.price_unit * (100 - record.voucher_id.value) / 100
            elif record.voucher_id.type == 'amount':
                record.total_amount = record.price_unit - record.voucher_id.value
        else:
            record.total_amount = record.price_unit

class online_course_mail(models.TransientModel):
    _name = 'online.course.mail'

    email_to = fields.Char(string='To', required=True)
    email_subject = fields.Char(string='Subject', required=True)
    email_body = fields.Html(string='Body', required=True)

    @api.multi
    def online_course_mail_send_email(self):
        # create mail message
        mail_message = self.env['mail.mail'].create({
            'subject': self.email_subject,
            'body_html': self.email_body,
            'email_to': self.email_to,
        })

        # send mail message
        try:
            mail_message.send()
        except Exception as e:
            raise ValidationError(str(e))

class online_course_set_invoice(models.Model):
    _inherit = 'account.invoice'
    online_course_id = fields.Many2one('online.course', string='Course')

class online_course_registration(models.Model):
    _inherit = 'event.registration'

    online_course_id = fields.Many2one('online.course', string='Online Course')
    def action_confirm(self):
            self.state = 'open'
            return True
class online_course_product(models.Model):
    _inherit = 'product.product'

    event_ids = fields.One2many('event.event','product_id', string="Event Id")

