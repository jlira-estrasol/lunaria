# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Space(models.Model):
    _name = 'space'
    _description = 'Space to be managed'

    name = fields.Char(
        required=True,
    )
    capacity = fields.Integer(
        required=True,
    )
    schedule_ids = fields.One2many(
        comodel_name='space.schedule',
        inverse_name='space_id',
        string=_('Schedules'),
    )
    anticipation = fields.Integer(
        string=_('Anticipation minutes allowed'),
        help=_('0 to be valid all day.'),
    )
    tolerance = fields.Integer(
        string=_('Tolerance minutes allowed'),
        help=_('0 to be valid all day.'),
    )

    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_('The capacity can not be negative.'))
