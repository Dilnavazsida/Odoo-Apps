/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { ImportRecords, importRecordsItem } from "@base_import/import_records/import_records";
import { exportAllItem } from "@web/views/list/export_all/export_all";
import { getModelFlags, getAccessRightsConfig } from "./access_rights_service";

const originalImportDisplayed = importRecordsItem.isDisplayed;
const originalExportDisplayed = exportAllItem.isDisplayed;

/**
 * Hide Import only when Disable Import is set — NOT when only Read-Only is set
 * (reference app keeps these as separate options).
 */
importRecordsItem.isDisplayed = async (env) => {
    const base = await originalImportDisplayed(env);
    if (!base) {
        return false;
    }
    const resModel =
        env.services?.action?.currentController?.props?.resModel ||
        env.searchModel?.resModel;
    if (!resModel) {
        return !getAccessRightsConfig().disable_import;
    }
    return !getModelFlags(resModel).disableImport;
};

exportAllItem.isDisplayed = async (env) => {
    const base = await originalExportDisplayed(env);
    if (!base) {
        return false;
    }
    const resModel =
        env.services?.action?.currentController?.props?.resModel ||
        env.searchModel?.resModel;
    if (!resModel) {
        return !getAccessRightsConfig().disable_export;
    }
    return !getModelFlags(resModel).disableExport;
};

/**
 * Keep the settings (gear) icon visible next to the list title even when ARM
 * hides Import / Export All and the cog would otherwise be empty.
 */
patch(CogMenu.prototype, {
    get hasItems() {
        if (super.hasItems) {
            return true;
        }
        const arm = getAccessRightsConfig();
        const viewType = this.env.config?.viewType;
        if (
            ["list", "kanban"].includes(viewType) &&
            (arm.is_readonly || arm.disable_import || arm.disable_export)
        ) {
            return true;
        }
        return false;
    },
});

void ImportRecords;
