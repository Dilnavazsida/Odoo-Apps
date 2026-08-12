# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
from odoo import api, fields, models


class AccessRightsManager(models.Model):
    _name = "access.rights.manager"
    _description = "Access Rights Manager"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    user_ids = fields.Many2many(
        "res.users",
        "access_rights_manager_users_rel",
        "rule_id",
        "user_id",
        string="Users",# -*- coding: utf-8 -*-
    )
    company_ids = fields.Many2many(
        "res.company",
        "access_rights_manager_company_rel",
        "rule_id",
        "company_id",
        string="Companies",
    )
    is_readonly = fields.Boolean(string="Read-Only")
    disable_import = fields.Boolean(string="Disable Import")
    disable_export = fields.Boolean(string="Disable Export")
    disable_delete = fields.Boolean(string="Disable Delete")
    disable_archive = fields.Boolean(string="Disable Archive/Unarchive")
    disable_developer_mode = fields.Boolean(string="Disable Developer Mode")
    hide_chatter = fields.Boolean(string="Hide Chatter")

    menu_line_ids = fields.One2many(
        "access.rights.menu.line", "rule_id", string="Hide Menu"
    )
    model_line_ids = fields.One2many(
        "access.rights.model.line", "rule_id", string="Model/Report/Action Access"
    )
    field_line_ids = fields.One2many(
        "access.rights.field.line", "rule_id", string="Field Access"
    )
    button_line_ids = fields.One2many(
        "access.rights.button.line", "rule_id", string="Button/Tab Access"
    )
    filter_line_ids = fields.One2many(
        "access.rights.filter.line", "rule_id", string="Filter / Group By Access"
    )
    domain_line_ids = fields.One2many(
        "access.rights.domain.line", "rule_id", string="Domain Access"
    )
    chatter_line_ids = fields.One2many(
        "access.rights.chatter.line", "rule_id", string="Hide Chatter by Model"
    )

    @api.model
    def _get_rules_for_user(self, user=None, company=None):
        user = user or self.env.user
        company = company or self.env.company
        if user._is_superuser() or user.has_group("base.group_system"):
            return self.browse()
        domain = [
            ("active", "=", True),
            ("user_ids", "in", user.id),
            "|",
            ("company_ids", "=", False),
            ("company_ids", "in", company.id),
        ]
        return self.sudo().with_context(arm_skip_rules=True).search(domain)

    @api.model
    def get_user_access_config(self):
        """Return a JSON-serialisable config for the current user (JS + Python)."""
        rules = self._get_rules_for_user()
        config = {
            "is_readonly": False,
            "disable_import": False,
            "disable_export": False,
            "disable_delete": False,
            "disable_archive": False,
            "disable_developer_mode": False,
            "hide_chatter": False,
            "hidden_menu_ids": [],
            "models": {},
            "fields": {},
            "buttons": {},
            "filters": {},
            "domains": {},
            "hide_chatter_models": [],
        }
        if not rules:
            return config

        config["is_readonly"] = any(rules.mapped("is_readonly"))
        # Each global checkbox is independent (same as reference app).
        config["disable_import"] = any(rules.mapped("disable_import"))
        config["disable_export"] = any(rules.mapped("disable_export"))
        config["disable_delete"] = any(rules.mapped("disable_delete"))
        config["disable_archive"] = any(rules.mapped("disable_archive"))
        config["disable_developer_mode"] = any(rules.mapped("disable_developer_mode"))
        config["hide_chatter"] = any(rules.mapped("hide_chatter"))

        config["hidden_menu_ids"] = list(
            set(rules.mapped("menu_line_ids.menu_id").ids)
        )

        for line in rules.mapped("model_line_ids"):
            model = line.model_id.model
            entry = config["models"].setdefault(
                model,
                {
                    "hide_create": False,
                    "hide_edit": False,
                    "hide_delete": False,
                    "hide_duplicate": False,
                    "hide_import": False,
                    "hide_export": False,
                    "hide_archive": False,
                    "hide_report_ids": [],
                    "hide_action_ids": [],
                },
            )
            entry["hide_create"] = entry["hide_create"] or line.hide_create or config["is_readonly"]
            entry["hide_edit"] = entry["hide_edit"] or line.hide_edit or config["is_readonly"]
            entry["hide_delete"] = entry["hide_delete"] or line.hide_delete or config["disable_delete"]
            # Duplicate = create copy → block with Read-Only (no separate global checkbox)
            entry["hide_duplicate"] = entry["hide_duplicate"] or line.hide_duplicate or config["is_readonly"]
            entry["hide_import"] = entry["hide_import"] or line.hide_import or config["disable_import"]
            entry["hide_export"] = entry["hide_export"] or line.hide_export or config["disable_export"]
            entry["hide_archive"] = entry["hide_archive"] or line.hide_archive or config["disable_archive"]
            entry["hide_report_ids"] = list(
                set(entry["hide_report_ids"] + line.hide_report_ids.ids)
            )
            entry["hide_action_ids"] = list(
                set(entry["hide_action_ids"] + line.hide_action_ids.ids)
            )

        for line in rules.mapped("field_line_ids"):
            model = line.model_id.model
            fields_cfg = config["fields"].setdefault(model, {})
            for field in line.field_ids:
                fcfg = fields_cfg.setdefault(
                    field.name,
                    {
                        "invisible": False,
                        "readonly": False,
                        "required": False,
                        "remove_external_link": False,
                    },
                )
                fcfg["invisible"] = fcfg["invisible"] or line.invisible
                fcfg["readonly"] = fcfg["readonly"] or line.readonly or config["is_readonly"]
                fcfg["required"] = fcfg["required"] or line.required
                fcfg["remove_external_link"] = (
                    fcfg["remove_external_link"] or line.remove_external_link
                )

        for line in rules.mapped("button_line_ids"):
            model = line.model_id.model
            btn_cfg = config["buttons"].setdefault(
                model, {"hide_buttons": [], "hide_pages": []}
            )
            # Match on both the technical name and the label, the arch may use
            # either one depending on the view.
            for key, elements in (
                ("hide_buttons", line.hide_button_ids),
                ("hide_pages", line.hide_page_ids),
            ):
                names = set(btn_cfg[key])
                for element in elements:
                    names.add(element.name)
                    if element.label:
                        names.add(element.label)
                btn_cfg[key] = list(names)

        for line in rules.mapped("filter_line_ids"):
            model = line.model_id.model
            flt_cfg = config["filters"].setdefault(
                model, {"hide_filters": [], "hide_groupbys": []}
            )
            for key, elements in (
                ("hide_filters", line.hide_filter_ids),
                ("hide_groupbys", line.hide_groupby_ids),
            ):
                names = set(flt_cfg[key])
                for element in elements:
                    names.add(element.name)
                    if element.label:
                        names.add(element.label)
                flt_cfg[key] = list(names)

        for line in rules.mapped("domain_line_ids"):
            model = line.model_id.model
            domains = config["domains"].setdefault(model, [])
            if line.domain:
                domains.append(line.domain)

        config["hide_chatter_models"] = list(
            set(
                rules.mapped("chatter_line_ids")
                .filtered("hide_chatter")
                .mapped("model_id.model")
            )
        )
        return config

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env.registry.clear_cache()
        return records

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
