odoo.define('space_control.pos', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    var _super_order = models.Order.prototype;

    models.load_models([{
        model: 'pos.order',
        fields: [
            'name',
        ],
        loaded: function (self, orders) { self.order = orders[0]; },
    }]);

    models.Order = models.Order.extend({
        load_server_data: function () {
            var self = this;
            self.models.push({
                model: 'space.schedule',
                fields: ['id'],
                loaded: function (self, schedules) {
                    self.schedules = schedules;
                },
            });
            return PosModelParent.load_server_data.apply(this, arguments);
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            var now = new Date();
            now = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
            var now_str = now.toISOString().substr(0, 16).replace(/[-T:]/g, '');
            this.key = now_str + this.generate_key_random(); // len = 20
            json.key = this.key;
            json.schedule_ids = this.schedule_ids;
            return json;
        },
        generate_key_random: function () {
            const len = 8; // TODO conf
            // Probability of collision
            // days = 16^8 = 4294967296
            // people = 200 per minute
            // p(n) = 0.00046333191 = 0.004%
            return 'x'.repeat(len).replace(/[x]/g, function (c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
    });
});
