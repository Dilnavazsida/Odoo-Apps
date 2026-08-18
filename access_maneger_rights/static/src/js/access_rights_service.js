/** @odoo-module **/

import { session } from "@web/session";

/**
 * Helpers to read Access Rights Manager restrictions for the current user.
 */
export function getAccessRightsConfig() {
        return session.access_rights_manager || {};
}

function _asList(value) {
    return Array.isArray(value) ? value : [];
}

export function isHiddenAction(action) {
    const config = getAccessRightsConfig();
    const ids = _asList(config.hidden_action_ids);
    const xmlids = _asList(config.hidden_action_xmlids);
    const paths = _asList(config.hidden_action_paths);
    if (action == null || action === false) {
        return false;
    }
    if (typeof action === "number") {
        return ids.includes(action);
    }
    if (typeof action === "string") {
        if (xmlids.includes(action) || paths.includes(action)) {
            return true;
        }
        const asNum = Number(action);
        return Number.isInteger(asNum) && ids.includes(asNum);
    }
    if (typeof action === "object") {
        if (action.id && ids.includes(action.id)) {
            return true;
        }
        if (action.xml_id && xmlids.includes(action.xml_id)) {
            return true;
        }
        if (action.path && paths.includes(action.path)) {
            return true;
        }
    }
    return false;
}

export function findFallbackMenu(menuService, preferredAppId) {
    const hiddenMenus = new Set(_asList(getAccessRightsConfig().hidden_menu_ids));
    const all = menuService.getAll().filter((m) => m && typeof m.id === "number" && m.actionID);
    const allowed = all.filter(
        (m) => !hiddenMenus.has(m.id) && !isHiddenAction(m.actionID) && !isHiddenAction(m.actionPath)
    );
    const appId = preferredAppId || menuService.getCurrentApp()?.id;
    const inApp = appId ? allowed.filter((m) => m.appID === appId && m.id !== appId) : [];
    const leaves = inApp.filter((m) => !m.children || m.children.length === 0);
    return leaves[0] || inApp[0] || allowed[0];
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
