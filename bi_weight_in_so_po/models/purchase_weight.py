# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	weight = fields.Float(string="Weight(kg)")
	new_price = fields.Float(string="Product Price")
	per_kg_price = fields.Float(string="Per Kg Price",compute="_compute_per_kg_price")

	def _compute_per_kg_price(self):
		per_kg_price = 0
		for line in self:
			if line.qty_received:
				per_kg_price = line.price_subtotal/(line.qty_received*line.product_qty)
			line.per_kg_price = per_kg_price

	def _prepare_account_move_line(self, move=False):
		self.ensure_one()
		aml_currency = move and move.currency_id or self.currency_id
		date = move and move.date or fields.Date.today()
		res = {
			'display_type': self.display_type or 'product',
			'name': '%s: %s' % (self.order_id.name, self.name),
			'product_id': self.product_id.id,
			'product_uom_id': self.product_uom.id,
			'quantity': self.product_qty,
			'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
			'tax_ids': [(6, 0, self.taxes_id.ids)],
			'purchase_line_id': self.id,
		}
		if self.analytic_distribution and not self.display_type:
			res['analytic_distribution'] = self.analytic_distribution
		return res

	@api.onchange('weight')
	def onchange_product_unit_price(self):
		for line in self:
			if line.product_id:
				params = {'order_id': line.order_id}
				seller = line.product_id._select_seller(
				partner_id=line.partner_id,
				quantity=line.product_qty,
				date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
				uom_id=line.product_uom,
				params=params)

				if not seller:
					unavailable_seller = line.product_id.seller_ids.filtered(
						lambda s: s.partner_id == line.order_id.partner_id)
					if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
						# Avoid to modify the price unit if there is no price list for this partner and
						# the line has already one to avoid to override unit price set manually.
						continue
					po_line_uom = line.product_uom or line.product_id.uom_po_id
					price_unit = line.env['account.tax']._fix_tax_included_price_company(
						line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
						line.product_id.supplier_taxes_id,
						line.taxes_id,
						line.company_id,
					)
					price_unit = line.product_id.cost_currency_id._convert(
						price_unit,
						line.currency_id,
						line.company_id,
						line.date_order or fields.Date.context_today(line),
						False
					)
					if line.price_unit == 0:
						line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
					line.new_price = line.price_unit
					if line.weight or line.product_id.weight: 
						if line.price_unit == 0:
							line.price_unit = line.new_price
					else:
						if line.product_id: 
							raise UserError(_("Product Weight Must Be Greter Than Zero"))
					continue

				price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
				price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
				price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
				line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
				
				line.new_price = line.price_unit
				if line.price_unit == 0:
					line.price_unit = line.new_price

	@api.depends('product_qty', 'product_uom', 'company_id')
	def _compute_price_unit_and_date_planned_and_name(self):
		for line in self:
			if not line.product_id or line.invoice_lines or not line.company_id:
				continue
			params = {'order_id': line.order_id}
			seller = line.product_id._select_seller(
				partner_id=line.partner_id,
				quantity=line.product_qty,
				date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
				uom_id=line.product_uom,
				params=params)

			if seller or not line.date_planned:
				line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

			if line.product_id and line.product_id.weight and line.weight:
				if line.price_unit == 0:
					line.price_unit = line.new_price
			else:
				if line.product_id: 
					raise UserError(_("Product Weight Must Be Greter Than Zero"))
		

			# If not seller, use the standard price. It needs a proper currency conversion.
			if not seller:
				unavailable_seller = line.product_id.seller_ids.filtered(
					lambda s: s.partner_id == line.order_id.partner_id)
				if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
					# Avoid to modify the price unit if there is no price list for this partner and
					# the line has already one to avoid to override unit price set manually.
					continue
				po_line_uom = line.product_uom or line.product_id.uom_po_id
				price_unit = line.env['account.tax']._fix_tax_included_price_company(
					line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
					line.product_id.supplier_taxes_id,
					line.taxes_id,
					line.company_id,
				)
				price_unit = line.product_id.currency_id._convert(
					price_unit,
					line.currency_id,
					line.company_id,
					line.date_order or fields.Date.context_today(line),
					False
				)
				if line.price_unit == 0:
					line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
				continue

			price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
			price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
			price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
			if line.price_unit == 0:
				line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)

			# record product names to avoid resetting custom descriptions
			default_names = []
			vendors = line.product_id._prepare_sellers({})
			for vendor in vendors:
				product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
				default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
			if not line.name or line.name in default_names:
				product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
				line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

	@api.onchange('product_id')
	def onchange_product_weight(self):
		for product in self:
			product.weight = product.product_id.weight

	@api.onchange('product_qty')
	def onchange_product_qty(self):
		for product in self:
			product.weight = product.weight*product.product_qty

	def _prepare_stock_moves(self, picking):
		res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
		for re in res:
			re['extra_weight'] = self.weight
		return res


class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	total_weight = fields.Float(string="Weight", readonly=True,compute="_compute_total_weight")
	weight_unit = fields.Char(string="kg", readonly=True)

	def _compute_total_weight(self):
		for rec in self:
			total_weight = 0
			for line in rec.order_line:
				if line.qty_received:
					total_weight += line.qty_received or 0.0
				else:
					total_weight += line.weight or 0.0
			rec.total_weight = total_weight

	def button_confirm(self):
		result = super(PurchaseOrder, self).button_confirm()
		for order in self:
			order.picking_ids.write({'total_weight': self.total_weight})
		return result

	@api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
	def  _compute_tax_totals(self):
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
