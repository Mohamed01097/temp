# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class AccountingTaxReport(models.TransientModel):
    _inherit = 'account.tax.report.wizard'

    tax_ids = fields.Many2many('account.tax', string="Taxes",required = True)
    customer_options = fields.Selection([
        ('with_total','With Total'),
        ('with_total_customer','Total Customer'),
        ('with_details_customer','Customer Details')
    ],default='with_details')

    def _print_report(self, data):
        if self._name =='account.tax.report.wizard':
            if self.customer_options and self.with_total:
                raise ValidationError(_('You Must Select Only Total OR Customer Options'))

        if self.tax_ids:
            data['form']['tax_ids'] = self.tax_ids.ids
        else:
            data['form']['tax_ids'] = self.env['account.tax'].search([]).ids

        data['form']['customer_options'] = self.customer_options
        if self._context.get('excel_report'):
            return self.env.ref('kb_extend_tax_report.action_report_account_tax_excel').report_action(
                self, data=data)
        else:
            return super(AccountingTaxReport, self)._print_report(data)

