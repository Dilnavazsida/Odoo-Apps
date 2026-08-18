# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
import logging

from lxml import etree

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccessRightsViewElement(models.Model):
    """Catalog of buttons, pages, filters and group-bys found in a model's views.

    Records are collected lazily (when a model is picked on a Button/Tab or
    Filter line) so the tag fields can offer suggestions instead of asking the
    user to type technical names by hand.
    """

    _name = "access.rights.view.element"
    _description = "Access Rights View Element"
    _order = "model_id, element_type, label, name"
    _rec_name = "display_name"

    model_id = fields.Many2one(
        "ir.model", string="Model", required=True, ondelete="cascade", index=True
    )
    element_type = fields.Selection(
        [
            ("button", "Button"),
            ("page", "Tab / Page"),
            ("filter", "Filter"),
            ("groupby", "Group By"),
        ],
        string="Type",
        required=True,
        index=True,
    )
    name = fields.Char(
        required=True, help="Technical name of the view element."
    )
    label = fields.Char(string="Label", help="Label displayed in the view.")
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _sql_constraints = [
        (
            "element_uniq",
            "UNIQUE (model_id, element_type, name)",
            "This view element already exists for that model.",
        ),
    ]

    @api.depends("name", "label")
    def _compute_display_name(self):
        for element in self:
            if element.label and element.label != element.name:
                element.display_name = f"{element.label} ({element.name})"
            else:
                element.display_name = element.label or element.name or ""

    @api.model
    def _extract_nodes_from_arch(self, arch, view_type, elements):
        if view_type in ("form", "list"):
            for node in arch.iter("button"):
                label = (node.get("string") or (node.text or "")).strip()
                name = node.get("name") or label
                if name:
                    elements.setdefault(("button", name), label or name)
            for node in arch.iter("page"):
                label = (node.get("string") or "").strip()
                name = node.get("name") or label
                if name:
                    elements.setdefault(("page", name), label or name)
        elif view_type == "search":
            for node in arch.iter("filter"):
                label = (node.get("string") or "").strip()
                name = node.get("name") or label
                if not name:
                    continue
                context = node.get("context") or ""
                element_type = "groupby" if "group_by" in context else "filter"
                prev = elements.get((element_type, name))
                if not prev or prev == name:
                    elements[(element_type, name)] = label or name
                elif label and label != name:
                    elements[(element_type, name)] = label

    @api.model
    def _collect_view_elements(self, model_name):
        """Return ``{(element_type, name): label}`` for the model's views.

        Search views are collected from every active search view of the model,
        not only the default one — Odoo often uses separate primary search views
        per action (e.g. Quotations vs Sales Orders).
        """
        elements = {}
        Model = self.env[model_name].with_context(arm_skip_rules=True)

        for view_type in ("form", "list"):
            try:
                arch = etree.fromstring(Model.get_view(view_type=view_type)["arch"])
            except Exception:  # noqa: BLE001
                _logger.debug(
                    "Access Rights Manager: no usable %s view for %s",
                    view_type,
                    model_name,
                )
                continue
            self._extract_nodes_from_arch(arch, view_type, elements)

        search_views = (
            self.env["ir.ui.view"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    ("model", "=", model_name),
                    ("type", "=", "search"),
                ]
            )
        )
        if search_views:
            for view in search_views:
                try:
                    arch = etree.fromstring(
                        Model.get_view(view_id=view.id, view_type="search")["arch"]
                    )
                except Exception:  # noqa: BLE001
                    _logger.debug(
                        "Access Rights Manager: cannot load search view %s for %s",
                        view.id,
                        model_name,
                    )
                    continue
                self._extract_nodes_from_arch(arch, "search", elements)
        else:
            try:
                arch = etree.fromstring(Model.get_view(view_type="search")["arch"])
                self._extract_nodes_from_arch(arch, "search", elements)
            except Exception:  # noqa: BLE001
                pass

        return elements

    @api.model
    def _sync_model_elements(self, model):
        """Create/update the catalog entries for ``model`` (an ``ir.model``)."""
        if not model or model.model not in self.env:
            return self.browse()
        elements = self._collect_view_elements(model.model)
        if not elements:
            return self.browse()

        catalog = self.sudo()
        existing = catalog.search([("model_id", "=", model.id)])
        known = {(rec.element_type, rec.name): rec for rec in existing}
        to_create = []
        for (element_type, name), label in elements.items():
            rec = known.get((element_type, name))
            if rec:
                if label and label != rec.label:
                    rec.label = label
            else:
                to_create.append(
                    {
                        "model_id": model.id,
                        "element_type": element_type,
                        "name": name,
                        "label": label,
                    }
                )
        if to_create:
            existing |= catalog.create(to_create)
        return existing
