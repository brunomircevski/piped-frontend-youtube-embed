<template>
    <nav
        class="fixed inset-x-0 bottom-0 z-40 border-t border-(--border) bg-(--surface)/90 pb-(--bottom-inset) backdrop-blur-md lg:hidden"
    >
        <div class="mx-auto flex h-14 max-w-xl">
            <template v-for="item in items" :key="item.label">
                <button
                    v-if="item.search"
                    type="button"
                    class="flex flex-1 cursor-pointer flex-col items-center justify-center gap-1 text-[11px] font-medium"
                    :class="route.name === 'SearchResults' ? 'text-(--text)' : 'text-muted'"
                    @click="openMobileSearch"
                >
                    <component :is="item.icon" class="text-lg" />
                    <span v-t="item.label" />
                </button>
                <router-link
                    v-else
                    :to="item.to"
                    class="flex flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium"
                    :class="isActive(item.to) ? 'text-(--text)' : 'text-muted'"
                >
                    <component :is="item.icon" class="text-lg" />
                    <span v-t="item.label" />
                </router-link>
            </template>
        </div>
    </nav>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { getPreferenceBoolean } from "@/composables/usePreferences.js";
import { openMobileSearch } from "@/composables/useMobileSearch.js";
import IconFeed from "~icons/fa6-solid/circle-play";
import IconSearch from "~icons/fa6-solid/magnifying-glass";
import IconList from "~icons/fa6-solid/list";
import IconHistory from "~icons/fa6-solid/clock-rotate-left";
import IconGear from "~icons/fa6-solid/gear";

const route = useRoute();

const items = computed(() => [
    { search: true, label: "titles.search", icon: IconSearch },
    { to: "/feed", label: "titles.feed", icon: IconFeed },
    { to: "/playlists", label: "titles.playlists", icon: IconList },
    getPreferenceBoolean("watchHistory", false)
        ? { to: "/history", label: "titles.history", icon: IconHistory }
        : { to: "/preferences", label: "titles.preferences", icon: IconGear },
]);

function isActive(path) {
    return route.path === path || route.path.startsWith(path + "/");
}
</script>
