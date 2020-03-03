# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_ticket = fields.Boolean(
        compute='_get_is_ticket_or_reservation',
        store=True,
    )
    is_reservation = fields.Boolean(
        compute='_get_is_ticket_or_reservation',
        store=True,
    )
    space_ids = fields.Many2many(
        comodel_name='space',
        string=_('Spaces'),
        compute='_get_sapace_ids',
        store=True,
    )
    subproduct_ids = fields.One2many(
        comodel_name='space.reservation.guest_relation',
        inverse_name='reservation_type_id',
    )

    @api.depends('subproduct_ids')
    def _get_sapace_ids(self):
        for record in self:
            if record.subproduct_ids:
                record.space_ids = []
                for sp in record.subproduct_ids:
                    record.space_ids += sp.product_id.space_ids

    @api.depends('pos_categ_id')
    def _get_is_ticket_or_reservation(self):
        for record in self:
            if record.pos_categ_id:
                record.is_ticket = record.pos_categ_id == self.env.ref('space_control.pos_category_ticket')
                record.is_reservation = record.pos_categ_id == self.env.ref('space_control.pos_category_reservation')
