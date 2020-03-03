# -*- coding: utf-8 -*-

from datetime import timedelta


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceScheduleDummy(models.TransientModel):
    _name = 'space.schedule.dummy'
    _description = 'Helper to make reservations'

    space_id = fields.Many2one(
        comodel_name='space',
        required=True,
    )
    start_datetime = fields.Datetime(
        required=True,
        string=_('Start'),
    )
    schedule_id = fields.Many2one(
        comodel_name='space.schedule',
        compute='_get_schedule',
        # domain=lambda self: ['space_id', '=', self.space_id.id] if self.space_id else [],
    )
    used = fields.Integer(
        related='schedule_id.used',
    )

    @api.depends('space_id', 'start_datetime')
    def _get_schedule(self):
        SpaceSchedule = self.env['space.schedule']
        for record in self:
            if record.space_id and record.start_datetime:
                record.schedule_id = SpaceSchedule.search([
                    ('space_id', '=', record.space_id.id),
                    ('start_datetime', '<=', record.start_datetime),
                    ('stop_datetime', '>', record.start_datetime),
                ], limit=1)
