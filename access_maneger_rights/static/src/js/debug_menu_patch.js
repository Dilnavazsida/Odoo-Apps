/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { ResConfigDevTool } from "@web/webclient/settings_form_view/widgets/res_config_dev_tool";
import { getAccessRightsConfig } from "./access_rights_service";

const config = getAccessRightsConfig();
if (config.disable_developer_mode) {
    document.documentElement.classList.add("arm-no-debug");
    const url = new URL(browser.location.href);
    if (odoo.debug) {
        url.searchParams.set("debug", "0");
        browser.location.replace(url.toString());
    } else if (url.searchParams.has("debug")) {
        url.searchParams.delete("debug");
        browser.location.replace(url.toString());
    }
}

patch(ResConfigDevTool.prototype, {
    setup() {
        super.setup(...arguments);
        if (getAccessRightsConfig().disable_developer_mode) {
            this.isDebug = false;
            this.isAssets = true;
            this.isTests = true;
        }
    },
});
