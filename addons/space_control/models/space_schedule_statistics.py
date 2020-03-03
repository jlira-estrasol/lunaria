# -*- coding: utf-8 -*-

from datetime import timedelta


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceSchedule(models.TransientModel):
    _name = 'space.schedule.statistics'
    _description = 'Auxiliary model to get schedule statistics.'

    start_datetime = fields.Datetime(
        default=fields.Datetime.now(),
        required=True,
    )
    stop_datetime = fields.Datetime(
        default=fields.Datetime.now(),
        required=True,
    )
    space_id = fields.Many2one(
        comodel_name='space',
    )
    schedule_ids = fields.Many2many(
        comodel_name="space.schedule",
        readonly=True,
    )

    def get_lines(self):
        SpaceSchedule = self.env['space.schedule']
        filter = [
            ('start_datetime', '>=', self.start_datetime),
            ('stop_datetime', '<=', self.stop_datetime),
        ]
        if self.space_id:
            filter.append(
                ('space_id', '=', self.space_id.id)
            )
        self.schedule_ids = SpaceSchedule.search(filter)
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
