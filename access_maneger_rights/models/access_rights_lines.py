# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Command
from odoo.tools.safe_eval import safe_eval


class Many2manyNoComodelFk(fields.Many2many):
    """Many2many that skips the foreign key on the comodel column.

    ``ir_actions`` is a PostgreSQL inheritance parent: window/server/client
    actions are physically stored in the child tables (``ir_act_window``, ...),
    so a foreign key pointing at ``ir_actions(id)`` rejects their ids.
    """

    def update_db_foreign_keys(self, model):
        if model._is_an_ordinary_table():
            model.pool.add_foreign_key(
                self.relation, self.column1, model._table, "id", "cascade",
                model, self._module, force=False,
            )


class AccessRightsMenuLine(models.Model):
    _name = "access.rights.menu.line"
    _description = "Access Rights Menu Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    menu_id = fields.Many2one(
        "ir.ui.menu", string="Menu", required=True, ondelete="cascade"
    )


class AccessRightsModelLine(models.Model):
    _name = "access.rights.model.line"
    _description = "Access Rights Model Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model_name = fields.Char(
        related="model_id.model",
        store=True,
        readonly=True,
        string="Model Technical Name",
    )
    hide_report_ids = fields.Many2many(
        "ir.actions.report",
        "access_rights_model_report_rel",
        "line_id",
        "report_id",
        string="Hide Reports",
        domain="[('model', '=', model_name)]",
        ondelete="cascade",
    )
    hide_action_ids = Many2manyNoComodelFk(
        "ir.actions.actions",
        "access_rights_model_action_rel",
        "line_id",
        "action_id",
        string="Hide Actions",
        domain="[('binding_model_id', '=', model_id), ('binding_type', '=', 'action')]",
    )
    hide_create = fields.Boolean(string="Hide Create")
    hide_edit = fields.Boolean(string="Hide Edit")
    hide_delete = fields.Boolean(string="Hide Delete")
    hide_duplicate = fields.Boolean(string="Hide Duplicate")
    hide_import = fields.Boolean(string="Hide Import")
    hide_export = fields.Boolean(string="Hide Export")
    hide_archive = fields.Boolean(string="Hide Archive/Unarchive")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.hide_report_ids = False
        self.hide_action_ids = False

    def unlink(self):
        # Clear M2M links first (relation rows only — never unlink ir.actions).
        self.write(
            {
                "hide_action_ids": [Command.clear()],
                "hide_report_ids": [Command.clear()],
            }
        )
        return super().unlink()

    def init(self):
        """Drop the stale ``action_id`` foreign key left by older versions.

        ``check_foreign_keys()`` only creates or updates expected keys, it never
        removes obsolete ones, so the constraint has to be dropped explicitly.
        """
        super().init()
        cr = self.env.cr
        cr.execute(
            """
            SELECT con.conname
              FROM pg_constraint con
              JOIN pg_class rel ON rel.oid = con.conrelid
              JOIN pg_attribute att
                ON att.attrelid = con.conrelid AND att.attnum = ANY (con.conkey)
             WHERE con.contype = 'f'
               AND rel.relname = 'access_rights_model_action_rel'
               AND att.attname = 'action_id'
               AND rel.relnamespace = current_schema::regnamespace
            """
        )
        connames = [row[0] for row in cr.fetchall()]
        for conname in connames:
            cr.execute(
                'ALTER TABLE "access_rights_model_action_rel" '
                f'DROP CONSTRAINT IF EXISTS "{conname}"'
            )
        if connames:
            cr.execute(
                "DELETE FROM ir_model_constraint WHERE name IN %s",
                (tuple(connames),),
            )


class AccessRightsFieldLine(models.Model):
    _name = "access.rights.field.line"
    _description = "Access Rights Field Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    field_ids = fields.Many2many(
        "ir.model.fields",
        "access_rights_field_line_fields_rel",
        "line_id",
        "field_id",
        string="Field",
        domain="[('model_id', '=', model_id)]",
        ondelete="cascade",
    )
    invisible = fields.Boolean(string="Invisible")
    readonly = fields.Boolean(string="Read-Only")
    required = fields.Boolean(string="Required")
    remove_external_link = fields.Boolean(string="Remove External Link")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.field_ids = False

    def unlink(self):
        self.write({"field_ids": [Command.clear()]})
        return super().unlink()


class AccessRightsButtonLine(models.Model):
    _name = "access.rights.button.line"
    _description = "Access Rights Button/Tab Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    hide_button_ids = fields.Many2many(
        "access.rights.view.element",
        "access_rights_button_line_button_rel",
        "line_id",
        "element_id",
        string="Hide Button",
        domain="[('model_id', '=', model_id), ('element_type', '=', 'button')]",
        ondelete="cascade",
    )
    hide_page_ids = fields.Many2many(
        "access.rights.view.element",
        "access_rights_button_line_page_rel",
        "line_id",
        "element_id",
        string="Hide Tab/Page",
        domain="[('model_id', '=', model_id), ('element_type', '=', 'page')]",
        ondelete="cascade",
    )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.hide_button_ids = False
        self.hide_page_ids = False
        # Fill the suggestion catalog so the tag fields propose the buttons and
        # tabs actually present in this model's views.
        self.env["access.rights.view.element"]._sync_model_elements(self.model_id)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        Element = self.env["access.rights.view.element"]
        for model in lines.mapped("model_id"):
            Element._sync_model_elements(model)
        return lines

    def write(self, vals):
        res = super().write(vals)
        if vals.get("model_id"):
            self.env["access.rights.view.element"]._sync_model_elements(
                self.env["ir.model"].browse(vals["model_id"])
            )
        return res

    def unlink(self):
        self.write(
            {
                "hide_button_ids": [Command.clear()],
                "hide_page_ids": [Command.clear()],
            }
        )
        return super().unlink()


class AccessRightsFilterLine(models.Model):
    _name = "access.rights.filter.line"
    _description = "Access Rights Filter / Group By Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    hide_filter_ids = fields.Many2many(
        "access.rights.view.element",
        "access_rights_filter_line_filter_rel",
        "line_id",
        "element_id",
        string="Hide Filters",
        domain="[('model_id', '=', model_id), ('element_type', '=', 'filter')]",
        ondelete="cascade",
    )
    hide_groupby_ids = fields.Many2many(
        "access.rights.view.element",
        "access_rights_filter_line_groupby_rel",
        "line_id",
        "element_id",
        string="Hide Group By",
        domain="[('model_id', '=', model_id), ('element_type', '=', 'groupby')]",
        ondelete="cascade",
    )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.hide_filter_ids = False
        self.hide_groupby_ids = False
        self.env["access.rights.view.element"]._sync_model_elements(self.model_id)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        Element = self.env["access.rights.view.element"]
        for model in lines.mapped("model_id"):
            Element._sync_model_elements(model)
        return lines

    def write(self, vals):
        res = super().write(vals)
        if vals.get("model_id"):
            self.env["access.rights.view.element"]._sync_model_elements(
                self.env["ir.model"].browse(vals["model_id"])
            )
        return res

    def unlink(self):
        self.write(
            {
                "hide_filter_ids": [Command.clear()],
                "hide_groupby_ids": [Command.clear()],
            }
        )
        return super().unlink()


class AccessRightsDomainLine(models.Model):
    _name = "access.rights.domain.line"
    _description = "Access Rights Domain Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model_technical_name = fields.Char(
        string="Model Technical Name",
        related="model_id.model",
        readonly=True,
    )
    domain = fields.Char(string="Assignment Domain", default="[]")

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.domain = "[]"

    def _get_domain_list(self):
        self.ensure_one()
        try:
            return safe_eval(self.domain or "[]")
        except Exception:
            return []

    @api.model
    def arm_preview_records(self, model_name, domain, user_ids, limit=1000):
        """Return the records the affected users will really see with ``domain``.

        The standard domain widget counts as the manager editing the rule, which
        is misleading: the targeted users are also subject to their own record
        rules, so the rule usually matches fewer records for them.
        """
        if not self.env.su and not self.env.user.has_group(
            "access_maneger_rights.group_access_rights_manager"
        ):
            raise AccessError(_("Only Access Rights managers can preview records."))
        empty = {"count": 0, "ids": [], "limited": False}
        if model_name not in self.env:
            return empty
        users = self.env["res.users"].browse(user_ids).exists()
        if not users:
            return empty

        limit = limit or 1000
        ids = set()
        for user in users:
            try:
                records = (
                    self.env[model_name]
                    .with_user(user)
                    .with_context(arm_skip_rules=True)
                    .search(domain or [], limit=limit + 1)
                )
            except AccessError:
                continue
            ids.update(records.ids)
        ids = sorted(ids)
        limited = len(ids) > limit
        ids = ids[:limit]
        return {"count": len(ids), "ids": ids, "limited": limited}


class AccessRightsChatterLine(models.Model):
    _name = "access.rights.chatter.line"
    _description = "Access Rights Chatter Line"

    rule_id = fields.Many2one(
        "access.rights.manager", required=True, ondelete="cascade"
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    hide_chatter = fields.Boolean(string="Hide Chatter", default=True)
