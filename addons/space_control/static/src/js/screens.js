odoo.define("space_control.screens", function (require) {
    "use strict";

    var screens = require("point_of_sale.screens");
    var rpc = require("web.rpc");
    var core = require('web.core');
    var models = require('point_of_sale.models');

    var _t = core._t;

    models.load_fields('product.product', [
        'space_ids',
    ]);

    var get_spaces = function () {
        var filter = [
        ]
        var fields = [
            'name',
            'id',
        ]
        return rpc.query({
            model: 'space',
            method: 'search_read',
            args: [filter, fields],
        })
    }

    var get_future_schedules_by_date = function (date) {
        var hours_delta = date.getTimezoneOffset() / 60;
        var start_datetime = new Date(date)
        start_datetime.setHours(start_datetime.getHours() + hours_delta);
        var stop_datetime = new Date(start_datetime)
        stop_datetime.setHours(23, 59, 59)
        window.start_datetime = start_datetime
        window.stop_datetime = stop_datetime
        var filter = [
            ['start_datetime', '>=', start_datetime],
            ['stop_datetime', '<=', stop_datetime],
            ['stop_datetime', '>', new Date()],
        ]
        var fields = [
            'start_datetime',
            'space_id',
            'availability',
        ]
        return rpc.query({
            model: 'space.schedule',
            method: 'search_read',
            args: [filter, fields],
        })
    }

    var insert_space_on_table = function (space, table) {
        var tbody = document.createElement('tbody');
        var tr = document.createElement('tr');
        var th = document.createElement('th');

        tbody.setAttribute("id", "space_" + space.id);
        tbody.setAttribute("class", "schedule_body");
        th.appendChild(document.createTextNode(space.name));
        th.setAttribute("id", "th_" + space.id);
        th.setAttribute("class", "space");
        th.setAttribute("colspan", "2");

        tr.appendChild(th);
        tbody.appendChild(tr);
        table.appendChild(tbody)
    }

    var insert_schedule_on_section = function (schedule, section) {
        var tr = document.createElement('tr');
        var td = document.createElement('td');

        tr.setAttribute("id", "schedule_" + schedule.id);
        tr.setAttribute("class", "tr_schedule");
        var start_datetime = new Date(schedule.start_datetime);
        var hours_delta = start_datetime.getTimezoneOffset() / 60;
        start_datetime.setHours(start_datetime.getHours() - hours_delta);
        td.appendChild(document.createTextNode(start_datetime.toLocaleTimeString()));
        tr.appendChild(td);
        td = document.createElement('td');
        td.appendChild(document.createTextNode(schedule.availability));
        tr.appendChild(td);
        section.appendChild(tr);
    }

    var generate_new_schedules_table = function (schedules_table, schedule_date_value) {
        $(".schedule_body").remove();
        get_spaces().then(function (spaces) {
            for (const space of spaces) {
                insert_space_on_table(space, schedules_table);
            }
            $("th.space").click(function () {
                $(this).parent().siblings().removeClass('selected');
            });
            get_future_schedules_by_date(schedule_date_value).then(function (schedules) {
                schedules.sort(function (a, b) { return a.start_datetime > b.start_datetime });
                for (const schedule of schedules) {
                    const section = document.getElementById('space_' + schedule.space_id[0]);
                    insert_schedule_on_section(schedule, section);
                }
                $(".tr_schedule").click(function () {
                    $(this).addClass('selected').siblings().removeClass('selected');
                });
            });
        });
    }

    var SpaceSchedule = screens.ActionButtonWidget.extend({
        template: 'SpaceSchedule',
        start: function () {
            var schedules_table = document.getElementById('schedules_table');
            $('#schedule_date').change(function () {
                generate_new_schedules_table(schedules_table, this.valueAsDate);
            });
        },
    });

    screens.define_action_button({
        'name': 'space_schedule',
        'widget': SpaceSchedule,
    });

    var get_selected_schedules = function () {
        var schedules = [];
        for (const tr of document.getElementsByClassName("tr_schedule selected")) {
            const space_id = tr.parentNode.getAttribute("id").substring("space_".length);
            const start_datetime = tr.childNodes[0].innerText;
            const availability = tr.childNodes[1].innerText;
            schedules.push({
                id: parseInt(tr.getAttribute("id").substring("schedule_".length)),
                space_id: parseInt(space_id),
                space_name: document.getElementById("th_" + space_id).innerText,
                start_datetime: start_datetime,
                availability: parseInt(availability),
            })
        }
        return schedules;
    }

    var check_overlap = function (schedules) {
        // TODO more flexible using time intersection instead of just start_date
        var times = Object.create(null);
        for (var i = 0; i < schedules.length; ++i) {
            var schedule = schedules[i].start_datetime;
            if (schedule in times) {
                return true;
            }
            times[schedule] = true;
        }
        return false;
    }

    var check_availability = function (schedules, total_tickets) {
        for (const schedule of schedules) {
            if (schedule.availability < total_tickets) {
                return schedule.space_name
            }
        }
        return false
    }

    var get_space_not_valid = function (space_ids, schedule_ids) {
        for (const schedule of schedule_ids) {
            if (!space_ids.has(schedule.space_id)) {
                return schedule.space_id;
            }
        }
        return false;
    }

    var get_space_not_used = function (space_ids, schedule_ids) {
        var spaces_used = new Set();
        for (const schedule of schedule_ids) {
            spaces_used.add(schedule.space_id);
        }
        for (const space of space_ids) {
            if (!spaces_used.has(space)) {
                return space;
            }
        }
        return false;
    }

    screens.ActionpadWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.pay').off('click');
            this.$('.pay').click(function () {
                var order = self.pos.get_order();
                var space_ids = new Set();
                var total_tickets = 0;
                for (var line of order.orderlines.models) {
                    line.product.space_ids.forEach(id => space_ids.add(id));
                    total_tickets += parseInt(line.quantity);
                }
                order.schedule_ids = get_selected_schedules();
                if (check_overlap(order.schedule_ids)) {
                    self.gui.show_popup('error', {
                        'title': _t('Schedules overlapping'),
                        'body': _t('Cant select two or more schedules at the same time.'),
                    });
                    return;
                }
                var space_not_valid = get_space_not_valid(space_ids, order.schedule_ids)
                if (space_not_valid) {
                    space_not_valid = document.getElementById("th_" + space_not_valid).textContent;
                    self.gui.show_popup('error', {
                        'title': _t('Space not valid'),
                        'body': _t('You have been selected a schedule for the space ' + space_not_valid + ' and the tickets selected does not allow that.'),
                    });
                    return;
                }
                const space_with_out_availability = check_availability(order.schedule_ids, total_tickets);
                if (space_with_out_availability) {
                    self.gui.show_popup('error', {
                        'title': _t('Schedule without availability'),
                        'body': _t('The space' + space_with_out_availability + ' does not have enough availability at that time.'),
                    });
                    return;
                }
                order.schedule_date = document.getElementById("schedule_date").value;
                var space_not_used = get_space_not_used(space_ids, order.schedule_ids);
                if (space_not_used) {
                    space_not_used = document.getElementById("th_" + space_not_used).textContent;
                    self.gui.show_popup('confirm', {
                        'title': _t('Spaces not used'),
                        'body': _t('You have been selected a ticket for the space ' + space_not_used + ' and there is no schedule selected for that.'),
                        confirm: function () {
                            self.gui.show_screen('payment');
                        },
                    });
                    return;
                }
                self.gui.show_screen('payment');
            });
        },
    });

    screens.ReceiptScreenWidget.include({
        show: function () {
            this._super();
            const order = this.pos.get_order();
            new QRCode("qrcode", {
                text: order.key,
                width: 128,
                height: 128,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.L
            });
        },
    });

    const load_schedules_table = function () {
        var schedule_date = document.getElementById("schedule_date");
        var schedules_table = document.getElementById('schedules_table');
        var today_tz = new Date();
        var hours_delta = today_tz.getTimezoneOffset() / 60;
        today_tz.setHours(today_tz.getHours() - hours_delta);
        schedule_date.valueAsDate = today_tz;
        generate_new_schedules_table(schedules_table, schedule_date.valueAsDate);
    }

    screens.ScreenWidget.include({
        show: function () {
            this._super();
            load_schedules_table();
        },
    });

    return {
        SpaceSchedule: SpaceSchedule,
    }
});
