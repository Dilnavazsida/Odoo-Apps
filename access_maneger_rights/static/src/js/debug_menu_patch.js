/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { ResConfigDevTool } from "@web/webclient/settings_form_view/widgets/res_config_dev_tool";
import { getAccessRightsConfig } from "./access_rights_service";

const config = getAccessRightsConfig();
if (config.disable_developer_mode) {
    const url = new URL(browser.location.href);
    if (url.searchParams.has("debug")) {
        url.searchParams.delete("debug");
        browser.location.replace(url.toString());
    }
}

patch(ResConfigDevTool.prototype, {
    setup() {
        super.setup(...arguments);
        if (getAccessRightsConfig().disable_developer_mode) {
            // Hide all "Activate" links by pretending assets/tests modes are already on
            // and debug is off so only nothing useful shows — template still renders
            // deactivate if isDebug; force isDebug false after strip above.
            this.isDebug = false;
            this.isAssets = true;
            this.isTests = true;
        }
    },
    activateDebug(value) {
        if (getAccessRightsConfig().disable_developer_mode) {
            return;
        }
        return super.activateDebug(value);
    },
});
