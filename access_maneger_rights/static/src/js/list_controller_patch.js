/** @odoo-module **/

import { onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { getModelFlags } from "./access_rights_service";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        const flags = getModelFlags(this.props.resModel);
        this._armFlags = flags;
        if (flags.disableExport) {
            this.isExportEnable = false;
            onWillStart(async () => {
                this.isExportEnable = false;
            });
        }
        // Archive only when Disable Archive is set (not implied by Read-Only)
        if (flags.disableArchive) {
            this.archiveEnabled = false;
        }
        // Read-Only / Hide Create → New + Duplicate only
        if (flags.hideCreate || flags.isReadonly) {
            this.activeActions = {
                ...this.activeActions,
                create: false,
                duplicate: false,
            };
        }
        // Delete only when Disable Delete is set (not implied by Read-Only)
        if (flags.disableDelete) {
            this.activeActions = {
                ...this.activeActions,
                delete: false,
            };
        }
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        const flags = this._armFlags || getModelFlags(this.props.resModel);
        if (flags.disableExport) {
            delete items.export;
        }
        if (flags.hideDuplicate || flags.isReadonly) {
            delete items.duplicate;
        }
        if (flags.disableArchive) {
            delete items.archive;
            delete items.unarchive;
        }
        if (flags.disableDelete) {
            delete items.delete;
        }
        return items;
    },
});
