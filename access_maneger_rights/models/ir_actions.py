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


class IrActionsActions(models.Model):
    _inherit = "ir.actions.actions"

    @api.model
    def get_bindings(self, model_name):
        result = super().get_bindings(model_name)
        config = self.env["access.rights.manager"].with_context(
            arm_skip_rules=True
        ).get_user_access_config()
        model_cfg = (config.get("models") or {}).get(model_name) or {}
        hide_action_ids = set(model_cfg.get("hide_action_ids") or [])
        hide_report_ids = set(model_cfg.get("hide_report_ids") or [])
        if not hide_action_ids and not hide_report_ids:
            return result

        filtered = {}
        for key, actions in result.items():
            kept = []
            for action in actions:
                action_id = action.get("id")
                if key == "report" and action_id in hide_report_ids:
                    continue
                if action_id in hide_action_ids or action_id in hide_report_ids:
                    continue
                kept.append(action)
            filtered[key] = kept
        return filtered
