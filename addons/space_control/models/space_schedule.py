# -*- coding: utf-8 -*-

from datetime import timedelta
import pytz


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceSchedule(models.Model):
    _name = 'space.schedule'
    _description = 'Instance of timetable'

    name = fields.Char(
        compute='_get_name',
        store=True,
        readonly=False,
    )
    space_id = fields.Many2one(
        comodel_name='space',
        required=True,
    )
    capacity = fields.Integer(
        compute='_get_space_values',
        store=True,
        readonly=False,
    )
    anticipation = fields.Integer(
        compute='_get_space_values',
        store=True,
        readonly=False,
    )
    tolerance = fields.Integer(
        compute='_get_space_values',
        store=True,
        readonly=False,
    )
    used = fields.Integer(
        compute='_get_used',
        store=True,
    )
    availability = fields.Integer(
        compute='_get_availability',
        store=True,
    )
    start_datetime = fields.Datetime(
        required=True,
        string=_('Start'),
    )
    stop_datetime = fields.Datetime(
        required=True,
        compute='_get_stop_datetime',
        inverse='_set_stop_datetime',
        store=True,
        string=_('Stop'),
    )
    duration = fields.Float(
        required=True,
    )
    in_past = fields.Boolean(
        compute='_get_in_past',
    )
    pos_order_ids = fields.Many2many(
        comodel_name='pos.order',
        string=_('Orders'),
    )
    ticket_ids = fields.Many2many(
        comodel_name='pos.order.line',
        compute='_get_ticket_ids',
        store=True,
        string=_('Tickets'),
    )
    reserved = fields.Boolean(
        default=False,
    )
    available = fields.Boolean(
        default=True,
    )
    used_kid = fields.Integer(
        compute='_get_used',
        store=True,
    )
    used_adult = fields.Integer(
        compute='_get_used',
        store=True,
    )
    used_elder = fields.Integer(
        compute='_get_used',
        store=True,
    )
    used_student = fields.Integer(
        compute='_get_used',
        store=True,
    )
    used_handicapped = fields.Integer(
        compute='_get_used',
        store=True,
    )

    def use_tickets(self):
        context = dict(self.env.context)
        context['schedule_to_use_id'] = self.id
        return {
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order.use_wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.depends('space_id', 'start_datetime', 'stop_datetime')
    def _get_name(self):
        user_tz = self.env.user.tz or pytz.utc.zone
        local = pytz.timezone(user_tz)
        for record in self:
            if not record.name and record.space_id and record.start_datetime and record.stop_datetime:
                duration = '{0:02.0f}:{1:02.0f}'.format(*divmod(record.duration * 60, 60))
                localized = record.start_datetime + local.utcoffset(record.start_datetime)
                record.name = _('{space} at {start} for {duration} hours').format(
                    space=record.space_id.name,
                    start=localized.strftime('%Y-%m-%d %H:%M'),
                    duration=str(duration),
                )

    @api.depends('start_datetime', 'duration')
    def _get_stop_datetime(self):
        for record in self:
            if record.start_datetime:
                duration = timedelta(hours=record.duration)
                record.stop_datetime = record.start_datetime + duration

    def _set_stop_datetime(self):
        for record in self:
            if record.stop_datetime and record.start_datetime:
                record.duration = (record.stop_datetime - record.start_datetime).seconds / (60 * 60)

    @api.depends('stop_datetime')
    def _get_in_past(self):
        for record in self:
            if record.stop_datetime:
                record.in_past = record.stop_datetime < fields.Datetime.now()

    @api.depends('ticket_ids')
    def _get_used(self):
        for record in self:
            record.used = sum(ticket.qty for ticket in record.ticket_ids)
            reference_kid = self.env.ref('space_control.product_attribute_type_kid')
            reference_adult = self.env.ref('space_control.product_attribute_type_adult')
            reference_elder = self.env.ref('space_control.product_attribute_type_elder')
            reference_student = self.env.ref('space_control.product_attribute_type_student')
            reference_handicapped = self.env.ref('space_control.product_attribute_type_handicapped')
            record.used_kid = sum(ticket.qty for ticket in record.ticket_ids.filtered(
                lambda ticket: ticket.product_id.product_template_attribute_value_ids[0].product_attribute_value_id == reference_kid
            ))
            record.used_adult = sum(ticket.qty for ticket in record.ticket_ids.filtered(
                lambda ticket: ticket.product_id.product_template_attribute_value_ids[0].product_attribute_value_id == reference_adult
            ))
            record.used_elder = sum(ticket.qty for ticket in record.ticket_ids.filtered(
                lambda ticket: ticket.product_id.product_template_attribute_value_ids[0].product_attribute_value_id == reference_elder
            ))
            record.used_student = sum(ticket.qty for ticket in record.ticket_ids.filtered(
                lambda ticket: ticket.product_id.product_template_attribute_value_ids[0].product_attribute_value_id == reference_student
            ))
            record.used_handicapped = sum(ticket.qty for ticket in record.ticket_ids.filtered(
                lambda ticket: ticket.product_id.product_template_attribute_value_ids[0].product_attribute_value_id == reference_handicapped
            ))

    @api.depends('ticket_ids', 'capacity', 'available', 'reserved')
    def _get_availability(self):
        for record in self:
            if not record.available or record.reserved:
                record.availability = 0
            else:
                record.availability = record.capacity - record.used

    def _set_duration(self):
        for record in self:
            if record.start_datetime:
                duration = timedelta(days=1, hours=record.duration)
                record.stop_datetime = record.start_datetime + duration

    @api.depends('space_id')
    def _get_space_values(self):
        for record in self:
            if record.space_id:
                record.capacity = record.space_id.capacity
                record.anticipation = record.space_id.anticipation
                record.tolerance = record.space_id.tolerance

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

    @api.depends('pos_order_ids')
    def _get_ticket_ids(self):
        for record in self:
            for order in record.pos_order_ids:
                record.ticket_ids += order.lines.filtered(
                    lambda line: record.space_id in line.product_id.space_ids and line.product_id.is_ticket
                )

    @api.model
    def check_availability(self, date, lines):
        schedules = {}
        for line in lines:
            product = self.env['product.product'].browse(line['id'])
            for space in product.space_ids:
                schedule = self.search([
                    ('space_id', '=', space.id),
                    ('start_datetime', '<=', date),
                    ('stop_datetime', '>', date),
                ], limit=1)
                if not schedule:
                    raise ValidationError(_('No function at {} for the space {}').format(date, space))
                if not schedules.get(schedule.id):
                    schedules[schedule.id] = schedule.availability
                schedules[schedule.id] -= line['qty']
                if schedules[schedule.id] < 0:
                    raise ValidationError(_('Not enough availability at {} for the space {}, max {}').format(date, space.name, schedule.availability))
        return True

    def toggle_available(self):
        self.available = not self.available

    def toggle_reserved(self):
        self.reserved = not self.reserved
