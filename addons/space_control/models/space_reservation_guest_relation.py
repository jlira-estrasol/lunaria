# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceReservationType(models.Model):
    _name = 'space.reservation.guest_relation'
    _description = 'Space Reservation Guest Relation'

    template_id = fields.Many2one(
        comodel_name='product.template',
    )
    reservation_type_id = fields.Integer()  # Just for legacy
    product_id = fields.Many2one(
        comodel_name='product.product',
        domain=[('is_ticket', '=', True)],
        required=True,
    )
    qty = fields.Integer(
        required=True,
    )
