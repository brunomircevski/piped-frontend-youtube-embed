<template>
    <header
        class="sticky top-0 z-40 border-b border-(--border) bg-(--surface)/85 backdrop-blur-md supports-backdrop-filter:bg-(--surface)/75"
    >
        <nav class="mx-auto flex h-14 w-full max-w-[1800px] items-center gap-3 px-3 sm:px-6">
            <div class="flex flex-1 justify-start">
                <router-link class="flex items-center text-2xl font-bold tracking-tight" to="/" aria-label="Piped"
                    ><img alt="" src="/img/icons/logo.svg" height="28" width="28" class="-mr-2 w-8" />iped</router-link
                >
            </div>
            <!-- A form, so the keyboard's search/enter key submits on Android too (no keypress there). -->
            <form
                role="search"
                class="relative flex w-full max-w-xl items-center max-md:hidden"
                @submit.prevent="submitSearch"
            >
                <i-fa6-solid-magnifying-glass class="pointer-events-none absolute left-4 text-sm text-muted" />
                <input
                    ref="videoSearch"
                    v-model="searchText"
                    class="input h-10 w-full rounded-full bg-(--surface-muted) px-10 dark:border-transparent"
                    type="text"
                    enterkeyhint="search"
                    :title="$t('actions.search')"
                    :placeholder="$t('actions.search')"
                    @keyup="onKeyUp"
                    @focus="onInputFocus"
                    @blur="onInputBlur"
                />
                <ClearButton v-if="searchText" @clear="searchText = ''" />
            </form>
            <!-- navigation bar for large screen devices -->
            <ul class="hidden list-none items-center gap-1 md:flex md:flex-1 md:justify-end">
                <li v-if="shouldShowTrending">
                    <router-link to="/trending" class="nav-link">
                        <i-fa6-solid-fire /><span v-t="'titles.trending'" class="max-xl:hidden" />
                    </router-link>
                </li>
                <li v-if="!shouldShowTrending">
                    <router-link to="/feed" class="nav-link">
                        <i-fa6-solid-play /><span v-t="'titles.feed'" class="max-xl:hidden" />
                    </router-link>
                </li>
                <li>
                    <router-link to="/playlists" class="nav-link">
                        <i-fa6-solid-list /><span v-t="'titles.playlists'" class="max-xl:hidden" />
                    </router-link>
                </li>
                <li v-if="shouldShowHistory">
                    <router-link to="/history" class="nav-link">
                        <i-fa6-solid-clock-rotate-left /><span v-t="'titles.history'" class="max-xl:hidden" />
                    </router-link>
                </li>
                <li>
                    <router-link to="/preferences" class="nav-link" :title="$t('titles.preferences')">
                        <i-fa6-solid-gear /><span v-t="'titles.preferences'" class="max-xl:hidden" />
                    </router-link>
                </li>
                <li v-if="shouldShowRegister">
                    <router-link v-t="'titles.register'" to="/register" class="nav-link" />
                </li>
                <li v-if="shouldShowLogin">
                    <router-link to="/login" class="ml-1 btn ring-1 ring-(--border) btn-ghost ring-inset">
                        <i-fa6-solid-circle-user class="text-base" /><span v-t="'titles.login'" />
                    </router-link>
                </li>
            </ul>
            <button
                class="btn btn-icon btn-ghost md:hidden"
                :aria-label="$t('actions.search')"
                @click="toggleMobileSearch"
            >
                <i-fa6-solid-magnifying-glass />
            </button>
            <button class="btn btn-icon btn-ghost md:hidden" aria-label="Menu" @click="showTopNav = !showTopNav">
                <i-fa6-solid-xmark v-if="showTopNav" />
                <i-fa6-solid-bars v-else />
            </button>
        </nav>
        <!-- navigation bar for mobile devices -->
        <div
            v-if="showTopNav"
            class="flex flex-col border-t border-(--border) p-2 *:flex *:w-full *:items-center *:gap-3 *:rounded-lg *:px-3 *:py-2.5 *:hover:bg-(--surface-muted) md:hidden"
            @click="showTopNav = false"
        >
            <router-link v-if="shouldShowTrending" to="/trending">
                <i-fa6-solid-fire class="w-4" />
                <i18n-t keypath="titles.trending"></i18n-t>
            </router-link>
            <router-link v-if="!shouldShowTrending" to="/feed">
                <i-fa6-solid-play class="w-4" />
                <i18n-t keypath="titles.feed"></i18n-t>
            </router-link>
            <router-link to="/playlists">
                <i-fa6-solid-list class="w-4" />
                <i18n-t keypath="titles.playlists"></i18n-t>
            </router-link>
            <router-link v-if="shouldShowHistory" to="/history">
                <i-fa6-solid-clock-rotate-left class="w-4" />
                <i18n-t keypath="titles.history"></i18n-t>
            </router-link>
            <router-link to="/preferences">
                <i-fa6-solid-gear class="w-4" />
                <i18n-t keypath="titles.preferences"></i18n-t>
            </router-link>
            <router-link v-if="shouldShowLogin" to="/login">
                <i-fa6-solid-user class="w-4" />
                <i18n-t keypath="titles.login"></i18n-t>
            </router-link>
            <router-link v-if="shouldShowRegister" to="/register">
                <i-fa6-solid-user-plus class="w-4" />
                <i18n-t keypath="titles.register"></i18n-t>
            </router-link>
        </div>
        <!-- search bar for mobile devices -->
        <form
            v-show="showMobileSearch"
            role="search"
            class="relative flex w-full items-center px-3 pb-2.5 md:hidden"
            @submit.prevent="submitSearch"
        >
            <i-fa6-solid-magnifying-glass class="pointer-events-none absolute left-7 text-sm text-muted" />
            <input
                ref="mobileSearch"
                v-model="searchText"
                class="input h-10 w-full rounded-full bg-(--surface-muted) px-10 dark:border-transparent"
                type="text"
                enterkeyhint="search"
                :title="$t('titles.search')"
                :placeholder="$t('titles.search')"
                @keyup="onKeyUp"
                @focus="onInputFocus"
                @blur="onInputBlur"
            />
            <ClearButton v-if="searchText" class="right-6!" @clear="searchText = ''" />
        </form>
        <SearchSuggestions
            v-show="(searchText || showSearchHistory) && suggestionsVisible"
            ref="searchSuggestions"
            :search-text="searchText"
            @searchchange="onSearchTextChange"
        />
    </header>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import SearchSuggestions from "./SearchSuggestions.vue";
import ClearButton from "./ui/ClearButton.vue";
import hotkeys from "hotkeys-js";
import { getAuthToken } from "@/composables/useApi.js";
import { getPreferenceBoolean } from "@/composables/usePreferences.js";
import { getHomepagePreference } from "@/composables/useMisc.js";
import { useConfig } from "@/composables/useConfig.js";
import { mobileSearchRequest } from "@/composables/useMobileSearch.js";

const router = useRouter();
const route = useRoute();

const videoSearch = ref(null);
const searchSuggestions = ref(null);

const searchText = ref("");
const suggestionsVisible = ref(false);
const showTopNav = ref(false);
const mobileSearch = ref(null);
const showMobileSearch = ref(route.name === "SearchResults");

function toggleMobileSearch() {
    showMobileSearch.value = !showMobileSearch.value;
    showTopNav.value = false;
    if (showMobileSearch.value) nextTick(() => mobileSearch.value?.focus());
}

// Bottom nav's search button: always open, and focus so the keyboard comes up.
watch(mobileSearchRequest, () => {
    showMobileSearch.value = true;
    showTopNav.value = false;
    nextTick(() => {
        mobileSearch.value?.focus();
        mobileSearch.value?.select();
    });
});

const { authConfig } = useConfig();
const registrationDisabled = computed(() => authConfig.value?.registrationDisabled === true);

const shouldShowLogin = computed(() => {
    return getAuthToken() == null;
});

const shouldShowRegister = computed(() => {
    return registrationDisabled.value == false ? shouldShowLogin.value : false;
});

const shouldShowHistory = computed(() => {
    return getPreferenceBoolean("watchHistory", false);
});

const shouldShowTrending = computed(() => {
    return getHomepagePreference() != "trending";
});

const showSearchHistory = computed(() => {
    return getPreferenceBoolean("searchHistory", false) && localStorage.getItem("search_history");
});

watch(
    () => route.fullPath,
    () => {
        updateSearchTextFromURLSearchParams();
    },
);

function updateSearchTextFromURLSearchParams() {
    const query = new URLSearchParams(window.location.search).get("search_query");
    if (query) onSearchTextChange(query);
}

function focusOnSearchBar() {
    hotkeys("ctrl+k", event => {
        event.preventDefault();
        videoSearch.value.focus();
    });
}

function onKeyUp(e) {
    if (e.key === "ArrowUp" || e.key === "ArrowDown") {
        e.preventDefault();
    }
    searchSuggestions.value.onKeyUp(e);
}

function onInputFocus() {
    if (showSearchHistory.value) searchSuggestions.value.refreshSuggestions();
    suggestionsVisible.value = true;
}

function onInputBlur() {
    setTimeout(() => (suggestionsVisible.value = false), 200);
}

function onSearchTextChange(text) {
    searchText.value = text;
}

function submitSearch() {
    // Closes the on-screen keyboard and the suggestions.
    document.activeElement?.blur();
    if (searchText.value) {
        router.push({
            name: "SearchResults",
            query: { search_query: searchText.value },
        });
    } else {
        router.push("/");
    }
    return;
}

onMounted(() => {
    updateSearchTextFromURLSearchParams();
    focusOnSearchBar();
});
</script>

<style></style>
