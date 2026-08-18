/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { menuService } from "@web/webclient/menus/menu_service";
import {
    getAccessRightsConfig,
    isHiddenAction,
    findFallbackMenu,
} from "./access_rights_service";

function hashAction(webClient) {
    return webClient.router?.current?.hash?.action;
}

function hashMenuId(webClient) {
    return Number(webClient.router?.current?.hash?.menu_id || 0) || undefined;
}

async function redirectToAllowedMenu(menuService, preferredAppId) {
    const fallback = findFallbackMenu(menuService, preferredAppId);
    if (fallback) {
        await menuService.selectMenu(fallback);
        return true;
    }
    return false;
}

patch(menuService, {
    async start(env) {
        const service = await super.start(...arguments);
        const origSelect = service.selectMenu.bind(service);
        service.selectMenu = async (menu) => {
            menu = typeof menu === "number" ? service.getMenu(menu) : menu;
            if (
                menu &&
                (isHiddenAction(menu.actionID) || isHiddenAction(menu.actionPath))
            ) {
                const fallback = findFallbackMenu(service, menu.appID);
                if (fallback && fallback.id !== menu.id) {
                    return origSelect(fallback);
                }
            }
            return origSelect(menu);
        };
        return service;
    },
});

patch(WebClient.prototype, {
    async loadRouterState() {
        const firstAction = hashAction(this);
        if (isHiddenAction(firstAction)) {
            if (await redirectToAllowedMenu(this.menuService, hashMenuId(this))) {
                return;
            }
        }
        await super.loadRouterState(...arguments);
        const current = this.actionService.currentController?.action;
        if (isHiddenAction(current)) {
            await redirectToAllowedMenu(this.menuService, hashMenuId(this));
        }
    },
});
