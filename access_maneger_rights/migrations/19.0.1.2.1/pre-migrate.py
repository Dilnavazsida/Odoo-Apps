# -*- coding: utf-8 -*-
"""Remove Profile Management tables/views left from earlier versions."""


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_ui_menu
         WHERE id IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'access_maneger_rights'
               AND name = 'menu_access_rights_profiles'
               AND model = 'ir.ui.menu'
         )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_act_window
         WHERE id IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'access_maneger_rights'
               AND name = 'action_access_rights_profile'
               AND model = 'ir.actions.act_window'
         )
        """
    )
    for table in (
        "access_rights_manager_profile_rel",
        "access_rights_profile_users_rel",
        "access_rights_profile_groups_rel",
        "access_rights_profile",
    ):
        cr.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'access_maneger_rights'
           AND (
                name LIKE '%access_rights_profile%'
                OR name = 'menu_access_rights_profiles'
                OR model = 'access.rights.profile'
           )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_access
         WHERE model_id IN (
            SELECT id FROM ir_model WHERE model = 'access.rights.profile'
         )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_fields
         WHERE model = 'access.rights.profile'
            OR (model = 'access.rights.manager' AND name = 'profile_ids')
        """
    )
    cr.execute("DELETE FROM ir_model WHERE model = 'access.rights.profile'")
