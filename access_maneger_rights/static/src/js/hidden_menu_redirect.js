/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { WebClient } from "@web/webclient/webclient";
import { menuService } from "@web/webclient/menus/menu_service";
import {
    getAccessRightsConfig,
    isHiddenAction,
    findFallbackMenu,
} from "./access_rights_service";

/**
 * Stale localStorage menus still contain hidden items until the next registry
 * bump. Drop the cache so load_menus reflects Hide Menu on this login/refresh.
 */
(function dropStaleMenuCache() {
    const hidden = getAccessRightsConfig().hidden_menu_ids || [];
    if (!hidden.length) {
        return;
    }
    const stored = browser.localStorage.getItem("webclient_menus");
    if (!stored) {
        return;
    }
    try {
        const menus = JSON.parse(stored);
        const stale = hidden.some((id) => menus[id] || menus[String(id)]);
        if (stale) {
            browser.localStorage.removeItem("webclient_menus");
            browser.localStorage.removeItem("webclient_menus_version");
        }
    } catch {
        // ignore invalid cache
    }
})();

function firstRouterAction() {
    return (
        router.current.actionStack?.[0]?.action ||
        router.current.action ||
        router.current.action_id
    );
}

function storedAppId() {
    return Number(browser.sessionStorage.getItem("menu_id") || 0) || undefined;
}

async function redirectToAllowedMenu(menuService) {
    const fallback = findFallbackMenu(menuService, storedAppId());
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
        const firstAction = firstRouterAction();
        if (isHiddenAction(firstAction)) {
            if (await redirectToAllowedMenu(this.menuService)) {
                return;
            }
        }
        await super.loadRouterState(...arguments);
        const current = this.actionService.currentController?.action;
        if (isHiddenAction(current)) {
            await redirectToAllowedMenu(this.menuService);
        }
    },
});
