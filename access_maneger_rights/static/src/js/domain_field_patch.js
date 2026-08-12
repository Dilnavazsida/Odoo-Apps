import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { DomainField, domainField } from "@web/views/fields/domain/domain_field";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";

/**
 * Domain widget for Access Rights Manager rules.
 *
 * The standard widget counts the matching records as the manager editing the
 * rule. The targeted users are also subject to their own record rules, so that
 * count is usually higher than what they will really see. This variant asks the
 * server for the records visible to the users of the rule instead.
 */
export class ArmDomainField extends DomainField {
    getRuleUserIds() {
        const root = this.props.record.model.root;
        const users = root && root.data && root.data.user_ids;
        return users && users.currentIds ? [...users.currentIds] : [];
    }

    async checkProps(props = this.props) {
        const resModel = this.getResModel(props);
        const userIds = this.getRuleUserIds();
        if (!resModel || !userIds.length) {
            this.armIds = null;
            return super.checkProps(props);
        }
        const domain = this.getEvaluatedDomain(props);
        if (domain.isInvalid) {
            this.armIds = null;
            this.updateState({ isValid: false, recordCount: 0, hasLimitedCount: false });
            return;
        }
        let result;
        try {
            result = await this.orm.silent.call(
                "access.rights.domain.line",
                "arm_preview_records",
                [resModel, domain, userIds],
                { limit: props.countLimit }
            );
        } catch {
            this.armIds = null;
            return super.checkProps(props);
        }
        this.armIds = result.ids;
        this.updateState({
            isValid: true,
            recordCount: result.count,
            hasLimitedCount: result.limited,
        });
    }

    onButtonClick() {
        if (!this.armIds) {
            return super.onButtonClick();
        }
        this.addDialog(
            SelectCreateDialog,
            {
                title: _t("Records visible to these users"),
                noCreate: true,
                multiSelect: false,
                resModel: this.getResModel(),
                domain: [["id", "in", this.armIds]],
                context: this.getContext(),
            },
            {
                onClose: () => this.checkProps(),
            }
        );
    }
}

export const armDomainField = {
    ...domainField,
    component: ArmDomainField,
    displayName: _t("Access Rights Domain"),
};

registry.category("fields").add("arm_domain", armDomainField);
