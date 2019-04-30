odoo.define('magento_bridge.tour', function(require) {
"use strict";

var core = require('web.core');
var tour = require('web_tour.tour');

var _t = core._t;

tour.register('magento_bridge_tour', {
    url: "/web",
}, [tour.STEPS.MENU_MORE, {
    trigger: '.o_app[data-menu-xmlid="magento_bridge.magento_parent_menu"], .oe_menu_toggler[data-menu-xmlid="magento_bridge.magento_parent_menu"]',
    content: _t('Start connecting your odoo with magento using <b>Magento odoo Bridge app</b>.'),
    position: 'bottom',
}, {
    trigger: ".o_mob_dashboard .o_dashboard_action[name=\"magento_bridge.magento_configure_tree_action\"]:last",
    extra_trigger: '.o_mob_dashboard',
    content:  _t("Click here to configure your magento connection."),
    position: "bottom"
},{
    trigger: ".o_list_button_add",
    extra_trigger: ".o_mob",
    content: _t("Let's create a new magento connection."),
    position: "right",
},
 {
    trigger: ".o_form_required",
    extra_trigger: '.oe_highlight',
    content:  _t("Enter magento base Url."),
    position: "top",
    run: "text Url",
}
, {
    trigger: ".o_address_street",
    extra_trigger: '.oe_highlight',
    content:  _t("Enter soap username"),
    position: "top",
    run: "text username",
}
, {
    trigger: ".o_address_city",
    extra_trigger: '.oe_highlight',
    content:  _t("Enter soap user password"),
    position: "top",
    run: "text password",
},
{
    trigger: ".o_mob_test",
    extra_trigger: ".o_mob",
    content: _t("Now test your magento connection."),
    position: "right",
}
, {
    trigger: ".o_mob_dashboard .o_dashboard_action[name=\"magento_bridge.magento_synchronization_action\"]",
    extra_trigger: '.o_mob_dashboard',
    content:  _t("Start bulk synchronization from Odoo to Magento."),
    position: "bottom"
}, {
    trigger: ".oe_link",
    extra_trigger: '.oe_highlight',
    content:  _t("View your magneto connection."),
    position: "bottom"
}

]);

});
