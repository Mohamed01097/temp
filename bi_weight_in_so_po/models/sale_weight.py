# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    weight = fields.Float(string="Weight(kg)", compute="_compute_weight")
        
    @api.onchange('product_id')
    def onchange_product_weight(self):
        for product in self:
            product.weight = product.product_id.weight

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty_(self):
        for product in self:
            product.weight = product.weight*product.product_uom_qty

    def _compute_weight(self):
        for line in self:
            weight = 0
            if line.product_id and line.product_id.weight:
                weight += (line.product_id.weight * line.product_uom_qty)
            line.weight = weight

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res.update({'weight': self.weight})
        return res

    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.product_uom_qty,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
        }
        analytic_account_id = self.order_id.analytic_account_id.id
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in res:
                res['analytic_distribution'][analytic_account_id] = res['analytic_distribution'].get(analytic_account_id, 0) + 100
            else:
                res['analytic_distribution'] = {analytic_account_id: 100}
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res



class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_weight = fields.Float(string="Weight", readonly=True, compute='_compute_total_weight')
    weight_unit = fields.Char(string="kg", readonly=True)

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'currency_id')
    def _compute_tax_totals(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            )
            total = 0
            for line in order.order_line:
                total +=line.price_subtotal
            order.tax_totals.update({'amount_untaxed':total,
                                    })
            
    def _compute_total_weight(self):
        for rec in self:
            total_weight = 0
            for line in rec.order_line:
                if line.qty_delivered:
                    total_weight += line.qty_delivered or 0.0
                else:
                    total_weight += line.weight or 0.0
            rec.total_weight = total_weight

    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for order in self:
            order.picking_ids.write({'total_weight': self.total_weight})
        return result
