# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpaceReservationType(models.TransientModel):
    _name = 'space.reservation'
    _description = 'Space Reservation'

    product_id = fields.Many2one(
        comodel_name='product.product',
        domain=[('is_reservation', '=', True)],
        required=True,
    )
    price = fields.Float(
        related='product_id.list_price',
    )
    space_ids = fields.Many2many(
        related='product_id.space_ids',
    )
    subproduct_ids = fields.One2many(
        related='product_id.subproduct_ids',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
    )
    schedule_dummy_ids = fields.Many2many(
        comodel_name='space.schedule.dummy',
        # inverse_name='reservation_id',
        compute='_get_schedule_dummy_ids',
        required=True,
        readonly=False,
        store=True,
    )

    @api.depends('space_ids')
    def _get_schedule_dummy_ids(self):
        for record in self:
            record.schedule_dummy_ids.unlink()
            for space in record.product_id.space_ids:
                ScheduleDummy = self.env['space.schedule.dummy']
                record.schedule_dummy_ids += ScheduleDummy.create({
                    'space_id': space.id,
                    'start_datetime': fields.Datetime.now(),
                })

    def _check_dummies(self):
        for dummy in self.schedule_dummy_ids:
            if not dummy.schedule_id:
                raise ValidationError(_('The space {} has no valid schedule selected.').format(dummy.space_id.name))
            if dummy.used:
                raise ValidationError(_('Schedule for space {} already have guests, please select other.').format(dummy.space_id.name))

    def make_reservation(self):
        self._check_dummies()
        name = '{} - {}'.format(self.partner_id.display_name, self.product_id.name)
        PoSOrder = self.env['pos.order']
        Session = self.env['pos.session']
        OrderLine = self.env['pos.order.line']
        Schedule = self.env['space.schedule']
        order = PoSOrder.create({
            'amount_paid': self.price,  # TODO imp
            'amount_return': 0,  # TODO imp
            'amount_tax': 0,  # TODO imp
            'amount_total': self.price,
            'company_id': self.env.user.company_id.id,
            'name': name,
            'session_id': Session.search([], limit=1).id,  # TODO imp
            'partner_id': self.partner_id.id,
        })
        for dummy in self.schedule_dummy_ids:
            order.schedule_ids += dummy.schedule_id
        for line in self.subproduct_ids:
            OrderLine.create({
                'order_id': order.id,
                'product_id': line.product_id.id,
                'price_unit': 0,
                'price_subtotal': 0,
                'price_subtotal_incl': 0,
                'qty': line.qty,
            })
        OrderLine.create({
            'order_id': order.id,
            'price_unit': self.product_id.list_price,
            'price_subtotal': self.product_id.list_price,
            'price_subtotal_incl': self.product_id.list_price,
            'product_id': self.product_id.id,
            'qty': 1,
        })
