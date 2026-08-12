/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { getModelFlags } from "./access_rights_service";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        const flags = getModelFlags(this.props.resModel);
        this._armFlags = flags;
        if (flags.hideCreate || flags.isReadonly) {
            this.canCreate = false;
        }
        if (flags.hideEdit || flags.isReadonly) {
            this.canEdit = false;
        }
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        const flags = this._armFlags || getModelFlags(this.props.resModel);
        if (flags.hideDuplicate || flags.isReadonly) {
            delete items.duplicate;
        }
        // Delete / Archive only when their own checkboxes are set
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
