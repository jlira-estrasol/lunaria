# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_ticket = fields.Boolean(
        related='product_id.is_ticket'
    )
    schedule_datetime = fields.Char(
    )
