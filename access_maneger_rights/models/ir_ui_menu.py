# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        config = self.env["access.rights.manager"].with_context(
            arm_skip_rules=True
        ).get_user_access_config()
        hidden = set(config.get("hidden_menu_ids") or [])
        if not hidden:
            return visible_ids
        all_menus = self.with_context(arm_skip_rules=True).browse(list(visible_ids)).sudo()
        to_hide = set()
        for menu in all_menus:
            current = menu
            while current:
                if current.id in hidden:
                    to_hide.add(menu.id)
                    break
                current = current.parent_id
        return visible_ids - to_hide
