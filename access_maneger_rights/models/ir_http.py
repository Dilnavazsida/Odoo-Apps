# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) NextGen.
#
#    For Module Support : next.gen.solutions2122@gmail.com
#
##############################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_public():
            return result
        AccessManager = self.env["access.rights.manager"].with_context(arm_skip_rules=True)
        result["access_rights_manager"] = AccessManager.get_user_access_config()
        return result
