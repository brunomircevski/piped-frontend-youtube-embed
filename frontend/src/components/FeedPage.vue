<template>
    <div class="mt-2 mb-5 flex items-center gap-3">
        <h1 v-t="'titles.feed'" class="page-title my-0" />
        <!-- Filters, sorting, the subscriptions list and RSS are tucked away until asked for. -->
        <button
            type="button"
            class="ml-auto btn"
            :aria-expanded="showOptions"
            aria-controls="feed-options"
            @click="showOptions = !showOptions"
        >
            <i-fa6-solid-sliders />
            <span v-t="'actions.filter'" />
            <span v-if="filtersActive" class="size-2 rounded-full bg-(--accent)" />
            <i-fa6-solid-chevron-down class="text-xs transition-transform" :class="{ 'rotate-180': showOptions }" />
        </button>
    </div>

    <div
        v-show="showOptions"
        id="feed-options"
        class="mb-5 flex flex-col gap-3 card text-sm md:flex-row md:flex-wrap md:items-center *:md:w-auto"
    >
        <label for="filters" class="flex items-center gap-2">
            <strong v-text="`${$t('actions.filter')}:`" />
            <select id="filters" v-model="selectedFilter" default="all" class="input grow" @change="onFilterChange()">
                <option v-for="filter in availableFilters" :key="filter" v-t="`video.${filter}`" :value="filter" />
            </select>
        </label>

        <label for="group-selector" class="flex items-center gap-2">
            <strong v-text="`${$t('titles.channel_groups')}:`" />
            <select id="group-selector" v-model="selectedGroupName" default="" class="input grow">
                <option v-t="`video.all`" value="" />
                <option
                    v-for="group in channelGroups"
                    :key="group.groupName"
                    :value="group.groupName"
                    v-text="group.groupName"
                />
            </select>
        </label>

        <span class="flex items-center gap-2">
            <SortingSelector by-key="uploaded" @apply="order => videos.sort(order)" />
        </span>

        <span class="flex gap-2 md:ml-auto">
            <router-link class="btn ring-1 ring-(--border) ring-inset" to="/subscriptions">
                <i-fa6-solid-users />
                <span v-t="'titles.subscriptions'" />
            </router-link>
            <a
                :href="getRssUrl"
                class="btn btn-icon ring-1 ring-(--border) ring-inset"
                :aria-label="$t('actions.rss_feed')"
                :title="$t('actions.rss_feed')"
            >
                <i-fa6-solid-rss />
            </a>
        </span>
    </div>

    <LoadingIndicatorPage :show-content="videosStore != null" class="video-grid">
        <template v-for="video in filteredVideos" :key="video.url">
            <VideoItem v-if="shouldShowVideo(video)" :is-feed="true" :item="video" @update:watched="onUpdateWatched" />
        </template>
    </LoadingIndicatorPage>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onDeactivated, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import VideoItem from "./VideoItem.vue";
import SortingSelector from "./SortingSelector.vue";
import LoadingIndicatorPage from "./LoadingIndicatorPage.vue";
import { authApiUrl, getAuthToken, isAuthenticated } from "@/composables/useApi.js";
import { getPreferenceBoolean, getPreferenceString, setPreference } from "@/composables/usePreferences.js";
import { fetchFeed, getUnauthenticatedChannels, fetchDeArrowContent } from "@/composables/useSubscriptions.js";
import { getChannelGroups } from "@/composables/useChannelGroups.js";
import { updateWatched } from "@/composables/useMisc.js";

const { t } = useI18n();

let currentVideoCount = 0;
const videoStep = 100;
const videosStore = ref(null);
const videos = ref([]);
const availableFilters = ["all", "shorts", "videos"];
const selectedFilter = ref("all");
const selectedGroupName = ref("");
const channelGroups = ref([]);
const showOptions = ref(false);

const filtersActive = computed(() => selectedFilter.value !== "all" || selectedGroupName.value !== "");

const getRssUrl = computed(() => {
    if (isAuthenticated()) return authApiUrl() + "/feed/rss?authToken=" + getAuthToken();
    else return authApiUrl() + "/feed/unauthenticated/rss?channels=" + getUnauthenticatedChannels();
});

const filteredVideos = computed(() => {
    const selectedGroup = channelGroups.value.filter(group => group.groupName == selectedGroupName.value);

    const vids = getPreferenceBoolean("hideWatched", false)
        ? videos.value.filter(video => !video.watched)
        : videos.value;

    return selectedGroupName.value == ""
        ? vids
        : vids.filter(video => selectedGroup[0].channels.includes(video.uploaderUrl.substr(-24)));
});

function loadMoreVideos() {
    if (!videosStore.value) return;
    currentVideoCount = Math.min(currentVideoCount + videoStep, videosStore.value.length);
    if (videos.value.length != videosStore.value.length) {
        fetchDeArrowContent(videosStore.value.slice(videos.value.length, currentVideoCount));
        videos.value = videosStore.value.slice(0, currentVideoCount);
    }
}

function handleScroll() {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - window.innerHeight) {
        loadMoreVideos();
    }
}

function onUpdateWatched(urls = null) {
    if (urls === null) {
        if (videos.value.length > 0) updateWatched(videos.value);
        return;
    }

    const subset = videos.value.filter(({ url }) => urls.includes(url));
    if (subset.length > 0) updateWatched(subset);
}

function shouldShowVideo(video) {
    switch (selectedFilter.value.toLowerCase()) {
        case "shorts":
            return video.isShort;
        case "videos":
            return !video.isShort;
        default:
            return true;
    }
}

function onFilterChange() {
    setPreference("feedFilter", selectedFilter.value);
}

onMounted(() => {
    fetchFeed().then(resp => {
        if (resp.error) {
            alert(resp.error);
            return;
        }

        videosStore.value = resp;
        loadMoreVideos();
        updateWatched(videos.value);
    });

    selectedFilter.value = getPreferenceString("feedFilter") ?? "all";

    if (!window.db) return;

    (async () => {
        const groups = await getChannelGroups();
        channelGroups.value.push(...groups);
    })();
});

onActivated(() => {
    document.title = t("titles.feed") + " - Piped";
    if (videos.value.length > 0) updateWatched(videos.value);
    window.addEventListener("scroll", handleScroll);
});

onDeactivated(() => {
    window.removeEventListener("scroll", handleScroll);
});

onUnmounted(() => {
    window.removeEventListener("scroll", handleScroll);
});
</script>
