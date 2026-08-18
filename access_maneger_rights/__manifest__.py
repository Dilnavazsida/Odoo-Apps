# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
{
    "name": "Access Rights Manager - Hide Menu, Field & Button",
    "version": "17.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Hide menus, fields, buttons, tabs, filters and control model/domain access rights per user.",
    "description": """
            Access Rights Manager - Hide Menu, Field & Button
            =================================================
            Customise field access (visible, required, read-only), model access (create, edit,
            delete, view, actions, duplicate), hide menus, buttons, tabs, filters and group by.
            Make users read-only, disable developer mode, hide chatter, and control
            import/export/archive globally.
    """,
    "author": "NextGen Services",
    "website": "https://nextgensolutions.infinityfreeapp.com/",
    "support": "next.gen.solutions2122@gmail.com",
    "depends": ["base", "web", "mail", "base_import"],
    "data": [
        "security/access_rights_security.xml",
        "security/ir.model.access.csv",
        "views/access_rights_view_element_views.xml",
        "views/access_rights_manager_views.xml",
        "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "access_maneger_rights/static/src/js/access_rights_service.js",
            "access_maneger_rights/static/src/js/hidden_menu_redirect.js",
            "access_maneger_rights/static/src/js/list_controller_patch.js",
            "access_maneger_rights/static/src/js/form_controller_patch.js",
            "access_maneger_rights/static/src/js/cog_menu_patch.js",
            "access_maneger_rights/static/src/js/debug_menu_patch.js",
            "access_maneger_rights/static/src/js/domain_field_patch.js",
            "access_maneger_rights/static/src/scss/access_rights.scss",
        ],
    },
    "images":["static/description/background.png"],
    "installable": True,
    "application": False,
    "currency": "EUR",
    "price": 25.98,
    "license": "OPL-1",
}
