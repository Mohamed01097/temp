# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'All in One Weight Details in Sales, Purchase, Delivery',
    'version': '16.0.0.8',
    'category': 'Sales',
    'summary': 'All in One Total Weight on Sale Order Weight on purchase order weight on delivery Total Weight on Sales Total Weight on purchase Total weight on delivery Calculate weight on sales calculate weight on delivery weight product weight all in one product weight',
    'description' :"""

      All in One Weight in odoo,
      Product Weight in odoo,
      Calculate Product Weight into Sale Order in odoo,
      Calculate Product Weight into Purchase Order in odoo,
      Calculate Product Weight into Delivery Order in odoo,
      Calculate Product Weight into Customer Invoice in odoo,
      Calculate Product Weight into Vendor Bill in odoo,
      Total product Weight in odoo,

    """,
    'author': 'BrowseInfo',
    "price": 15,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['sale_management','purchase','stock','account'],
    'data': [
        'report/report_template.xml',
        'views/sale_weight_views.xml',
        'views/purchase_weight_views.xml',
        'views/stock_weight_views.xml',
        'views/account_weight_views.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/XN9JyZqUST0',
    "images":['static/description/Banner.gif'],
    'license': 'OPL-1',
}
