from odoo import api, models, _,fields


class Reportfields(models.AbstractModel):
    _inherit = 'account.common.report'
    
    tax = fields.Selection([
        ('15', '15%'),
        ('5', '5%'),
    ], required=True, string='Tax Amount')
