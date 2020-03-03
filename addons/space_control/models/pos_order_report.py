# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models


class POSOrderReport(models.Model):
    _name = "pos.order.report"
    _description = "POS Order Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Order Reference', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    qty = fields.Integer('Qty', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    untaxed_amount_to_invoice = fields.Float('Untaxed Amount To Invoice', readonly=True)
    untaxed_amount_invoiced = fields.Float('Untaxed Amount Invoiced', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)

    discount = fields.Float('Discount %', readonly=True)
    discount_amount = fields.Float('Discount Amount', readonly=True)

    order_id = fields.Many2one('pos.order', 'Order #', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            l.product_id as product_id,
            sum(l.qty) as qty,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            count(*) as nbr,
            s.name as name,
            s.date_order as date,
            s.state as state,
            s.partner_id as partner_id,
            s.company_id as company_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            s.pricelist_id as pricelist_id,
            p.product_tmpl_id,
            l.discount as discount,
            sum((l.price_unit * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)) as discount_amount,
            s.id as order_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
                pos_order_line l
                      join pos_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.order_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.state,
            s.company_id,
            s.pricelist_id,
            p.product_tmpl_id,
            l.discount,
            s.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
