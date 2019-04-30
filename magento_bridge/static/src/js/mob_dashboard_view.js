odoo.define('magento_bridge.MobDashboard', function (require) {
"use strict";

var core = require('web.core');
var formats = require('web.formats');
var Model = require('web.Model');
var session = require('web.session');
var KanbanView = require('web_kanban.KanbanView');

var QWeb = core.qweb;

var _t = core._t;
var _lt = core._lt;

var MagentoBridgeDashboardView = KanbanView.extend({
    display_name: _lt('MOB Dashboard'),
    icon: 'fa-dashboard',
    searchview_hidden: true,
    events: {
        'click .o_dashboard_action': 'on_dashboard_action_clicked',
    },

    fetch_data: function() {
        return $.when();
    },

    render: function() {
        var super_render = this._super;
        var self = this;
        var values = {};

        return this.fetch_data().then(function(result){
            new Model('mob.dashboard').call('get_connection_info')
            .then(function(res){
                values = res;
                var mob_dashboard = QWeb.render('magento_bridge.MobDashboard', {
                    widget: self,
                    connrecs : values,
                });
            super_render.call(self);
            $(mob_dashboard).prependTo(self.$el);
            });
        });

    },

    on_dashboard_action_clicked: function(ev){
        ev.preventDefault();

        var $action = $(ev.currentTarget);
        var action_name = $action.attr('name');
        var action_extra = $action.data('extra');
        var additional_context = {};
        if (action_name === 'magento_bridge.magento_configure_tree_action') {
            if (action_extra === 'inactive'){
                additional_context.search_default_inactive = 1;
            }else if(action_extra === 'all'){
                additional_context.active_test = false;
            }
        }
        if (action_name === 'magento_bridge.magento_configure_tree_action_2') {
          action_name = 'magento_bridge.magento_configure_tree_action'
          if(action_extra === 'connected'){
              additional_context.search_default_success = 1;
          }else if(action_extra === 'error'){
              additional_context.search_default_error = 1;
          }
        }

        this.do_action(action_name, {additional_context: additional_context});
    },

});

core.view_registry.add('magento_bridge_dashboard', MagentoBridgeDashboardView);

return MagentoBridgeDashboardView;

});
