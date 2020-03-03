# -*- coding: utf-8 -*-

from datetime import datetime


from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    schedule_ids = fields.Many2many(
        comodel_name='space.schedule',
    )
    schedule_used_ids = fields.Many2many(
        comodel_name='space.schedule',
        relation='pos_order_space_schedule_used_rel',
        readonly=True,
    )
    key = fields.Char(
        index=True,
        readonly=True,
    )

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['key'] = ui_order['key']
        order_fields['schedule_ids'] = [schedule['id'] for schedule in ui_order['schedule_ids']]
        return order_fields
