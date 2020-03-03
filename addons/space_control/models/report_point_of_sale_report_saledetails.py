# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        result = super(ReportSaleDetails, self).get_sale_details(date_start, date_stop, config_ids, session_ids)
        for product in result['products']:
            product_id = self.env['product.product'].browse(product['product_id'])
            product['product_name'] = product_id.display_name
        return result
