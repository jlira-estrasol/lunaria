# -*- coding: utf-8 -*-

from datetime import timedelta
from dateutil import rrule


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceTimetable(models.TransientModel):
    _name = 'space.schedule.wizard'
    _description = 'Multiple schedules'

    def _default_spaces(self):
        return self.env['space'].browse(self._context.get('active_ids'))

    space_ids = fields.Many2many(
        comodel_name='space',
        default=_default_spaces,
        string=_('Space'),
    )
    start_datetime = fields.Datetime(
        required=True,
        string=_('Start'),
    )
    stop_datetime = fields.Datetime(
        required=True,
        string=_('Valid until'),
    )
    duration = fields.Float(
        default=1,  # TODO setting
        required=True,
    )
    mo = fields.Boolean(
        default=False,  # TODO setting
        string=_('Mon'),
    )
    tu = fields.Boolean(
        default=True,  # TODO setting
        string=_('Tue'),
    )
    we = fields.Boolean(
        default=True,  # TODO setting
        string=_('Wed'),
    )
    th = fields.Boolean(
        default=True,  # TODO setting
        string=_('Thu'),
    )
    fr = fields.Boolean(
        default=True,  # TODO setting
        string=_('Fri'),
    )
    sa = fields.Boolean(
        default=True,  # TODO setting
        string=_('Sat'),
    )
    su = fields.Boolean(
        default=True,  # TODO setting
        string=_('Sun'),
    )

    def generate_schedules(self):
        weekdays = [
            ('mo', 0),
            ('tu', 1),
            ('we', 2),
            ('th', 3),
            ('fr', 4),
            ('sa', 5),
            ('su', 6)
        ]
        days = [number for day, number in weekdays if self[day]]
        rr = rrule.rrule(
            dtstart=self.start_datetime,
            freq=rrule.WEEKLY,
            byweekday=days,
            until=self.stop_datetime,
        )
        SpaceSchedule = self.env['space.schedule']
        for space in self.space_ids:
            for day in rr:
                # TODO check if already exist
                duration = timedelta(hours=self.duration)
                SpaceSchedule.create({
                    'space_id': space.id,
                    'start_datetime': day,
                    'stop_datetime': day + duration,
                    'duration': duration.seconds / (60 * 60),
                })

    @api.constrains('start_datetime', 'stop_datetime')
    def _check_dates(self):
        for record in self:
            if record.start_datetime and record.stop_datetime:
                if record.stop_datetime <= record.start_datetime:
                    raise ValidationError(_('The stop date must be later than start date.'))

    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_('The capacity can not be negative.'))
