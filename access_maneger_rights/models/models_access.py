# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
from lxml import etree

from odoo import api, models
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _


_ARM_EXEMPT_PREFIXES = (
    "ir.",
    "bus.",
    "base.",
    "base_import.",
    "web.",
    "web_editor.",
    "publisher_warranty.",
    "access.rights.",
)
_ARM_EXEMPT_MODELS = frozenset(
    {
        "access.rights.manager",
        "res.users",
        "res.users.log",
        "res.users.settings",
        "res.users.apikeys",
        "res.users.apikeys.description",
        "res.device",
        "res.device.log",
        "res.lang",
        "res.company",
        "res.groups",
        "res.groups.privilege",
        "res.currency",
        "mail.presence",
        "mail.guest",
    }
)


class BaseAccessRights(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _arm_is_internal_model(self):
        return self._name == "access.rights.manager" or (
            self._name and self._name.startswith("access.rights.")
        )

    @api.model
    def _arm_is_exempt_model(self):
        """Skip ARM CRUD rules on technical models (login/session would break otherwise)."""
        name = self._name or ""
        if not name or self._arm_is_internal_model():
            return True
        if getattr(self, "_abstract", False) or getattr(self, "_transient", False):
            return True
        if name in _ARM_EXEMPT_MODELS or name.startswith("res.users"):
            return True
        return name.startswith(_ARM_EXEMPT_PREFIXES)

    @api.model
    def _arm_should_enforce(self):
        if self.env.su or self.env.context.get("arm_skip_rules"):
            return False
        if self._arm_is_exempt_model():
            return False
        return True

    @api.model
    def _arm_get_config(self):
        return (
            self.env["access.rights.manager"]
            .with_context(arm_skip_rules=True)
            .get_user_access_config()
        )

    @api.model
    def _arm_model_flags(self):
        config = self._arm_get_config()
        model_cfg = (config.get("models") or {}).get(self._name) or {}
        return config, model_cfg

    @api.model
    def get_views(self, views, options=None):
        result = super().get_views(views, options=options)
        if self.env.context.get("arm_skip_rules") or self._arm_is_exempt_model():
            return result
        config, model_cfg = self._arm_model_flags()
        if not config:
            return result

        hide_action_ids = set(model_cfg.get("hide_action_ids") or [])
        hide_report_ids = set(model_cfg.get("hide_report_ids") or [])
        for view in result.get("views", {}).values():
            toolbar = view.get("toolbar") or {}
            if toolbar.get("action") and hide_action_ids:
                toolbar["action"] = [
                    a for a in toolbar["action"] if a.get("id") not in hide_action_ids
                ]
            if toolbar.get("print") and hide_report_ids:
                toolbar["print"] = [
                    a for a in toolbar["print"] if a.get("id") not in hide_report_ids
                ]
            view["toolbar"] = toolbar

        result["access_rights_manager"] = {
            "is_readonly": config.get("is_readonly"),
            "disable_import": config.get("disable_import") or model_cfg.get("hide_import"),
            "disable_export": config.get("disable_export") or model_cfg.get("hide_export"),
            "disable_delete": config.get("disable_delete") or model_cfg.get("hide_delete"),
            "disable_archive": config.get("disable_archive") or model_cfg.get("hide_archive"),
            "hide_create": config.get("is_readonly") or model_cfg.get("hide_create"),
            "hide_edit": config.get("is_readonly") or model_cfg.get("hide_edit"),
            "hide_duplicate": config.get("is_readonly") or model_cfg.get("hide_duplicate"),
            "hide_chatter": config.get("hide_chatter")
            or self._name in (config.get("hide_chatter_models") or []),
            "model": self._name,
        }
        return result

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if self.env.context.get("arm_skip_rules") or self._arm_is_exempt_model():
            return result
        config, model_cfg = self._arm_model_flags()
        if not any(
            [
                config.get("is_readonly"),
                config.get("hide_chatter"),
                model_cfg,
                (config.get("fields") or {}).get(self._name),
                (config.get("buttons") or {}).get(self._name),
                (config.get("filters") or {}).get(self._name),
                self._name in (config.get("hide_chatter_models") or []),
            ]
        ):
            return result

        arch = etree.fromstring(result["arch"])
        self._arm_apply_field_rules(arch, config)
        self._arm_apply_button_page_rules(arch, config)
        self._arm_apply_search_filter_rules(arch, config, view_type)
        self._arm_apply_chatter_rules(arch, config, view_type)
        self._arm_apply_create_edit_flags(arch, config, model_cfg, view_type)
        result["arch"] = etree.tostring(arch, encoding="unicode")
        return result

    @api.model
    def _arm_apply_field_rules(self, arch, config):
        fields_cfg = (config.get("fields") or {}).get(self._name) or {}
        if not fields_cfg:
            return
        for node in arch.xpath("//field"):
            name = node.get("name")
            if not name or name not in fields_cfg:
                continue
            fcfg = fields_cfg[name]
            if fcfg.get("invisible"):
                node.set("invisible", "1")
                node.set("column_invisible", "1")
            if fcfg.get("readonly"):
                node.set("readonly", "1")
            if fcfg.get("required"):
                node.set("required", "1")
            if fcfg.get("remove_external_link"):
                node.set("options", "{'no_open': True, 'no_create': True}")

    @api.model
    def _arm_apply_button_page_rules(self, arch, config):
        btn_cfg = (config.get("buttons") or {}).get(self._name) or {}
        hide_buttons = {b.lower() for b in (btn_cfg.get("hide_buttons") or [])}
        hide_pages = {p.lower() for p in (btn_cfg.get("hide_pages") or [])}
        if hide_buttons:
            for node in arch.xpath("//button"):
                candidates = [
                    (node.get("name") or "").lower(),
                    (node.get("string") or "").lower(),
                    (node.text or "").strip().lower(),
                ]
                if any(c and c in hide_buttons for c in candidates):
                    node.set("invisible", "1")
        if hide_pages:
            for node in arch.xpath("//page"):
                candidates = [
                    (node.get("name") or "").lower(),
                    (node.get("string") or "").lower(),
                ]
                if any(c and c in hide_pages for c in candidates):
                    node.set("invisible", "1")

    @api.model
    def _arm_apply_search_filter_rules(self, arch, config, view_type):
        if view_type != "search":
            return
        flt_cfg = (config.get("filters") or {}).get(self._name) or {}
        hide_filters = {f.lower() for f in (flt_cfg.get("hide_filters") or [])}
        hide_groupbys = {g.lower() for g in (flt_cfg.get("hide_groupbys") or [])}
        if not hide_filters and not hide_groupbys:
            return
        for node in list(arch.xpath("//filter")):
            candidates = {
                (node.get("name") or "").lower(),
                (node.get("string") or "").lower(),
            }
            candidates.discard("")
            context = node.get("context") or ""
            is_groupby = "group_by" in context
            hide_set = hide_groupbys if is_groupby else hide_filters
            if candidates & hide_set:
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)

    @api.model
    def _arm_apply_chatter_rules(self, arch, config, view_type):
        if view_type != "form":
            return
        hide = config.get("hide_chatter") or self._name in (
            config.get("hide_chatter_models") or []
        )
        if not hide:
            return
        for node in arch.xpath(
            "//div[contains(@class,'oe_chatter')]|//chatter|//*[@name='mail_thread' or @name='message_ids']"
        ):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)

    @api.model
    def _arm_apply_create_edit_flags(self, arch, config, model_cfg, view_type):
        hide_create = config.get("is_readonly") or model_cfg.get("hide_create")
        hide_edit = config.get("is_readonly") or model_cfg.get("hide_edit")
        hide_delete = config.get("disable_delete") or model_cfg.get("hide_delete")
        hide_import = config.get("disable_import") or model_cfg.get("hide_import")
        hide_export = config.get("disable_export") or model_cfg.get("hide_export")
        if view_type in ("list", "tree", "kanban"):
            if hide_create:
                arch.set("create", "false")
            if hide_edit:
                arch.set("edit", "false")
            if hide_delete:
                arch.set("delete", "false")
            if hide_import:
                arch.set("import", "false")
            if hide_export:
                arch.set("export_xlsx", "false")
        elif view_type == "form":
            if hide_create:
                arch.set("create", "false")
            if hide_edit:
                arch.set("edit", "false")
            if hide_delete:
                arch.set("delete", "false")
            if hide_import:
                arch.set("import", "false")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._arm_should_enforce():
            config = self._arm_get_config()
            extra_domains = (config.get("domains") or {}).get(self._name) or []
            parsed = []
            for dom in extra_domains:
                if isinstance(dom, str):
                    try:
                        dom = safe_eval(dom)
                    except Exception:
                        continue
                if dom:
                    parsed.append(dom)
            if parsed:
                domain = expression.AND([domain] + parsed)
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid,
        )

    @api.model_create_multi
    def create(self, vals_list):
        if self._arm_should_enforce():
            config, model_cfg = self._arm_model_flags()
            if config.get("is_readonly") or model_cfg.get("hide_create"):
                raise AccessError(
                    _("You are not allowed to create records on this model.")
                )
        return super().create(vals_list)

    def write(self, vals):
        if self._arm_should_enforce():
            config, model_cfg = self._arm_model_flags()
            if config.get("is_readonly") or model_cfg.get("hide_edit"):
                raise AccessError(
                    _("You are not allowed to edit records on this model.")
                )
            if "active" in vals and (
                config.get("disable_archive") or model_cfg.get("hide_archive")
            ):
                raise AccessError(
                    _("You are not allowed to archive/unarchive records.")
                )
        return super().write(vals)

    def unlink(self):
        if self._arm_should_enforce():
            config, model_cfg = self._arm_model_flags()
            if config.get("disable_delete") or model_cfg.get("hide_delete"):
                raise AccessError(
                    _("You are not allowed to delete records on this model.")
                )
        return super().unlink()

    def copy(self, default=None):
        if self._arm_should_enforce():
            config, model_cfg = self._arm_model_flags()
            if config.get("is_readonly") or model_cfg.get("hide_duplicate"):
                raise AccessError(
                    _("You are not allowed to duplicate records on this model.")
                )
        return super().copy(default=default)

    def copy_data(self, default=None):
        if self._arm_should_enforce():
            config, model_cfg = self._arm_model_flags()
            if config.get("is_readonly") or model_cfg.get("hide_duplicate"):
                raise AccessError(
                    _("You are not allowed to duplicate records on this model.")
                )
        return super().copy_data(default=default)
