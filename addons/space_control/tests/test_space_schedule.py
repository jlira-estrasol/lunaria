# -*- coding: utf-8 -*-

from datetime import timedelta
import logging


from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields


_logger = logging.getLogger(__name__)


class TestSpaceSchedule(TransactionCase):
    def test_create(self):
        Space = self.env['space']
        space = Space.create({
            'name': 'Space',
            'capacity': 1,
        })
        Schedule = self.env['space.schedule']
        duration = timedelta(hours=2)
        schedule = Schedule.create({
            'space_id': space.id,
            'capacity': space.capacity,
            'start_datetime': fields.Datetime.now(),
            'stop_datetime': fields.Datetime.now() + duration,
            'duration': duration.seconds / (60 * 60),
        })
        return schedule

    def test_mod_duration(self):
        schedule = self.test_create()
        new_duration = 3
        duration = timedelta(hours=new_duration)
        schedule.duration = new_duration
        self.assertEqual(schedule.stop_datetime, fields.Datetime.now() + duration)

    def test_in_past(self):
        schedule = self.test_create()
        tomorrow = fields.Datetime.now() + timedelta(days=1)
        schedule.start_datetime = tomorrow
        schedule.stop_datetime = tomorrow + timedelta(hours=2)

        self.assertIs(schedule.in_past, False)
        yesterday = fields.Datetime.now() - timedelta(days=1)
        schedule.start_datetime = yesterday
        schedule.stop_datetime = yesterday + timedelta(hours=2)
        self.assertIs(schedule.in_past, True)

    def test_capacity(self):
        schedule = self.test_create()
        with self.assertRaises(ValidationError):
            schedule.capacity = -1
