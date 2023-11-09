# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _


class StockMove(models.Model):
    _inherit = "stock.move"

    weight = fields.Float(string="Weight(kg)", compute="_compute_weight",readonly=False,store=True)
    extra_weight = fields.Float(string="Weight(kg) ")

    @api.onchange('product_id')
    def onchange_product_weight(self):
        for product in self:
            product.weight = product.product_id.weight

    @api.depends('product_id')
    def _compute_weight(self):
        weight = 0
        for line in self:
            if line.product_id and line.product_id.weight:
                weight += (line.product_id.weight * line.product_uom_qty or line.quantity_done)
            line.weight = weight


class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_weight = fields.Float(string="Weight", readonly=True, compute="_compute_total_weight")
    weight_unit = fields.Char(string="kg", readonly=True)
    check_weight =fields.Boolean(string="Check weight",compute="_check_purchase_weight")

    def _compute_total_weight(self):
        for rec in self:
            total_weight = 0
            if rec.purchase_id : 
                for line in rec.move_ids_without_package:
                    if line.quantity_done:
                        total_weight += line.quantity_done or 0.0
                    else:
                        total_weight += line.extra_weight or 0.0
                rec.total_weight = total_weight
            else:
                for line in rec.move_ids_without_package:
                    if line.quantity_done:
                        total_weight += line.quantity_done or 0.0
                    else:
                        total_weight += line.weight or 0.0
                rec.total_weight = total_weight

    def _check_purchase_weight(self):
        for rec in self:
            if rec.purchase_id:
                rec.check_weight = True
            else:
                rec.check_weight = False
