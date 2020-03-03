# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSpace(TransactionCase):
    def test_create(self):
        Space = self.env['space']
        space = Space.create({
            'name': 'Space',
            'capacity': 1,
        })
        self.assertEqual(space.name, 'Space')
        self.assertEqual(space.capacity, 1)

    def test_constraint_capacity_negative(self):
        Space = self.env['space']
        with self.assertRaises(ValidationError):
            Space.create({
                'name': 'Space',
                'capacity': -1,
            })
