# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class POSOrderUseWizard(models.TransientModel):
    _name = 'pos.order.use_wizard'
    _description = 'Multiple schedules'

    key = fields.Char(
        compute='_get_key',
        readonly=False,
        required=True,
        store=True,
    )
    order_id = fields.Many2one(
        comodel_name='pos.order',
        compute='_get_order',
        readonly=False,
        required=True,
        store=True,
    )
    schedule_ids = fields.Many2many(
        related='order_id.schedule_ids',
    )
    schedule_to_use_id = fields.Many2one(
        comodel_name='space.schedule',
        default=lambda self: self._context.get('schedule_to_use_id', False),
        required=True,
    )
    schedule_used_ids = fields.Many2many(
        related='order_id.schedule_used_ids',
    )
    ticket_ids = fields.One2many(
        comodel_name='pos.order.line',
        related='order_id.lines',
    )
    prev_ticket_ids = fields.One2many(
        comodel_name='pos.order.line',
        related='prev_order_id.lines',
    )
    prev_order_id = fields.Many2one(
        comodel_name='pos.order',
        default=lambda self: self._context.get('prev_order_id', False),
        readonly=True,
    )
    error = fields.Text(
        default=lambda self: self._context.get('error', False),
        readonly=True,
    )

    @api.onchange('key')
    def _get_order(self):
        self.order_id = self.env['pos.order'].search([('key', '=', self.key)], limit=1) if self.key else False

    def mark_as_used(self):
        user_tz = self.env.user.tz or pytz.utc.zone
        local = pytz.timezone(user_tz)
        now = today = fields.Datetime.now()
        today = (now + local.utcoffset(now)).replace(hour=0, minute=0, second=0) - local.utcoffset(now)
        tomorrow = (now + local.utcoffset(now)).replace(hour=23, minute=59, second=59) - local.utcoffset(now)
        for record in self:
            if record.order_id:
                record.error = False
                schedule = record.schedule_to_use_id
                anticipation = timedelta(minutes=schedule.anticipation)
                tolerance = timedelta(minutes=schedule.tolerance)
                if schedule.start_datetime < today or schedule.start_datetime > tomorrow:
                    record.error = _('The schedule for {} is not for today.').format(schedule.space_id.name)
                if schedule.anticipation and now + anticipation < schedule.start_datetime:
                    record.error = _('The schedule for {} is for later today.').format(schedule.space_id.name)
                elif schedule.tolerance and now - tolerance > schedule.start_datetime:
                    record.error = _('The schedule for {} has expired.').format(schedule.space_id.name)
                if record.schedule_to_use_id not in record.schedule_ids:
                    record.error = _('The schedule {} is not available for this ticket.').format(record.schedule_to_use_id.name)
                if record.schedule_to_use_id in record.schedule_used_ids:
                    record.error = _('The schedule {} was already used.').format(record.schedule_to_use_id.name)
                if not record.error:
                    record.order_id.schedule_used_ids |= record.schedule_to_use_id
                context = dict(self.env.context)
                context['schedule_to_use_id'] = record.schedule_to_use_id.id
                context['prev_order_id'] = record.order_id.id
                context['error'] = record.error
                return {
                    'context': context,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': self._name,
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
            else:
                raise ValidationError(_('Select an order.'))
