/** @odoo-module **/

import { session } from "@web/session";

/**
 * Helpers to read Access Rights Manager restrictions for the current user.
 */
export function getAccessRightsConfig() {
    return session.access_rights_manager || {};
}

export function getModelFlags(resModel) {
    const config = getAccessRightsConfig();
    const modelCfg = (config.models && config.models[resModel]) || {};
    return {
        isReadonly: !!config.is_readonly,
        disableImport: !!(config.disable_import || modelCfg.hide_import),
        disableExport: !!(config.disable_export || modelCfg.hide_export),
        disableDelete: !!(config.disable_delete || modelCfg.hide_delete),
        disableArchive: !!(config.disable_archive || modelCfg.hide_archive),
        disableDeveloperMode: !!config.disable_developer_mode,
        hideCreate: !!(config.is_readonly || modelCfg.hide_create),
        hideEdit: !!(config.is_readonly || modelCfg.hide_edit),
        hideDuplicate: !!(config.is_readonly || modelCfg.hide_duplicate),
        hideChatter: !!(
            config.hide_chatter ||
            (config.hide_chatter_models || []).includes(resModel)
        ),
        modelCfg,
        config,
    };
}
