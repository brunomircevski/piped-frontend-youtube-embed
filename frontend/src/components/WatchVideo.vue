<template>
    <div v-if="video && isEmbed" class="absolute top-0 left-0 z-50 size-full bg-black">
        <YouTubeEmbed
            v-if="useYoutubeEmbed"
            ref="youtubeEmbed"
            :video-id="getVideoId()"
            :start-time="embedStartTime"
            :sponsors="sponsors"
            :loop="selectedAutoLoop"
            @timeupdate="onTimeUpdate"
        />
        <VideoPlayer
            v-else
            ref="videoPlayer"
            :video="video"
            :sponsors="sponsors"
            :selected-auto-play="false"
            :selected-auto-loop="selectedAutoLoop"
            :is-embed="isEmbed"
        />
    </div>
    <div id="theaterModeSpot" class="mb-1 has-[>*]:mb-6"></div>
    <LoadingIndicatorPage :show-content="video != null && !isEmbed" class="w-full">
        <ErrorHandler v-if="video && video.error" :message="video.message" :error="video.error" />
        <Transition>
            <ToastComponent v-if="shouldShowToast" @dismissed="dismiss">
                <i18n-t keypath="info.next_video_countdown">{{ counter }}</i18n-t>
            </ToastComponent>
        </Transition>
        <div v-show="!video.error" class="flex gap-6">
            <div class="min-w-0 flex-auto" :style="dragFade">
                <Teleport defer to="#theaterModeSpot" :disabled="!theaterMode || isMobile">
                    <div class="relative flex flex-row max-lg:-mx-3 max-lg:-mt-4 sm:max-lg:-mx-6">
                        <!-- GlobalPlayer draws the embed over this placeholder -->
                        <div
                            v-if="usesGlobalPlayer"
                            :ref="setSlot"
                            class="aspect-video max-h-[75vh] w-full min-w-0 flex-auto max-lg:max-h-svh"
                        />
                        <keep-alive v-else>
                            <VideoPlayer
                                ref="videoPlayer"
                                :video="video"
                                :sponsors="sponsors"
                                :selected-auto-play="selectedAutoPlayEnabled"
                                :selected-auto-loop="selectedAutoLoop"
                                @timeupdate="onTimeUpdate"
                                @ended="onVideoEnded"
                                @navigate-next="navigateNext"
                            />
                        </keep-alive>
                    </div>
                </Teleport>

                <!-- video title -->
                <h1 class="mt-3 text-xl/snug font-semibold wrap-break-word" v-text="video.title" />

                <!-- channel + actions -->
                <div class="mt-3 flex flex-col gap-3">
                    <!-- channel on the left, playback speed on the right (its own row on phones) -->
                    <div class="flex flex-wrap items-center gap-3">
                        <div class="flex min-w-0 items-center gap-3">
                            <router-link :to="video.uploaderUrl ?? '/'" class="shrink-0">
                                <UiAvatar :src="video.uploaderAvatar" :name="video.uploader" :size="40" />
                            </router-link>
                            <div class="min-w-0 leading-tight">
                                <router-link
                                    v-if="video.uploaderUrl"
                                    class="flex items-center gap-1 font-semibold"
                                    :to="video.uploaderUrl"
                                >
                                    <span class="truncate" v-text="video.uploader" />
                                    <i-fa6-solid-circle-check
                                        v-if="video.uploaderVerified"
                                        class="shrink-0 text-xs text-muted"
                                    />
                                </router-link>
                                <div
                                    v-if="video.uploaderSubscriberCount >= 0"
                                    v-t="{
                                        path: 'info.subscriber_count',
                                        args: { count: numberFormat(video.uploaderSubscriberCount) },
                                    }"
                                    class="text-xs text-muted"
                                />
                            </div>
                            <button
                                v-t="`actions.${subscribed ? 'unsubscribe' : 'subscribe'}`"
                                class="ml-1 btn"
                                :class="subscribed ? '' : 'btn-primary'"
                                @click="subscribeHandler"
                            />
                            <a
                                v-if="video.uploaderUrl"
                                :aria-label="$t('actions.rss_feed')"
                                :title="$t('actions.rss_feed')"
                                :href="`${apiUrl()}/feed/unauthenticated/rss?channels=${video.uploaderUrl.split('/')[2]}`"
                                target="_blank"
                                class="btn btn-icon text-muted btn-ghost max-sm:hidden"
                            >
                                <i-fa6-solid-rss />
                            </a>
                        </div>

                        <!-- playback speed (with Loop on phones) -->
                        <div
                            v-if="usesGlobalPlayer || isMobile"
                            class="flex items-center gap-2 text-sm *:h-9 *:rounded-full max-lg:w-full lg:ml-auto"
                        >
                            <label v-if="isMobile" for="chkAutoLoop" class="chip shrink-0 cursor-pointer">
                                <UiCheckbox id="chkAutoLoop" v-model="selectedAutoLoop" />
                                <span v-t="'actions.loop'" />
                            </label>
                            <template v-if="usesGlobalPlayer">
                                <span
                                    v-t="'actions.playback_speed'"
                                    class="flex items-center text-muted max-lg:hidden"
                                />
                                <div
                                    class="segmented h-full max-w-full scrollbar-none overflow-x-auto *:shrink-0"
                                    role="group"
                                    :aria-label="$t('actions.playback_speed')"
                                >
                                    <button
                                        v-for="rate in SPEEDS"
                                        :key="rate"
                                        type="button"
                                        :aria-pressed="player.rate === rate"
                                        @click="embed?.setPlaybackSpeed(rate)"
                                        v-text="`${rate}×`"
                                    />
                                </div>
                            </template>
                        </div>
                    </div>

                    <div
                        class="flex scrollbar-none items-center gap-2 overflow-x-auto max-sm:-mx-3 max-sm:w-[calc(100%+1.5rem)] max-sm:px-3 sm:flex-wrap"
                    >
                        <template v-if="!isMobile">
                            <label for="chkAutoLoop" class="btn shrink-0 cursor-pointer">
                                <UiCheckbox id="chkAutoLoop" v-model="selectedAutoLoop" />
                                <span v-t="'actions.loop'" />
                            </label>
                            <button class="btn shrink-0" @click="toggleTheaterMode">
                                <i-fa6-solid-compress v-if="theaterMode" />
                                <i-fa6-solid-expand v-else />
                                <span v-text="theaterMode ? 'Default view' : 'Theater mode'" />
                            </button>
                            <button v-if="usesGlobalPlayer" class="btn shrink-0" @click="minimizePlayer(router)">
                                <i-fa6-solid-down-left-and-up-right-to-center />
                                <span v-t="'actions.miniplayer'" />
                            </button>
                        </template>
                        <div
                            v-if="video.likes >= 0"
                            class="flex shrink-0 items-center rounded-full bg-(--surface-muted) text-sm font-medium lg:ml-auto"
                        >
                            <span class="flex items-center gap-2 py-2 pr-3 pl-4" :title="addCommas(video.likes)">
                                <i-fa6-solid-thumbs-up />
                                {{ numberFormat(video.likes) }}
                            </span>
                            <span class="h-5 w-px bg-(--border)" />
                            <span
                                class="flex items-center gap-2 py-2 pr-4 pl-3"
                                :title="video.dislikes >= 0 ? addCommas(video.dislikes) : ''"
                            >
                                <i-fa6-solid-thumbs-down />
                                {{ video.dislikes >= 0 ? numberFormat(video.dislikes) : "" }}
                            </span>
                        </div>
                        <span v-else v-t="'video.ratings_disabled'" class="chip shrink-0 lg:ml-auto" />
                        <button class="btn shrink-0" @click="showShareModal = !showShareModal">
                            <i-fa6-solid-share />
                            <span v-t="'actions.share'" />
                        </button>
                        <button class="btn shrink-0" @click="showModal = !showModal">
                            <i-fa6-solid-circle-plus />
                            <span v-t="'actions.playlist'" />
                        </button>
                        <button
                            v-if="usesGlobalPlayer"
                            class="btn shrink-0"
                            :aria-pressed="player.audioMode"
                            @click="setAudioMode(!player.audioMode)"
                        >
                            <i-fa6-solid-tv v-if="player.audioMode" />
                            <i-fa6-solid-headphones v-else />
                            <span v-t="player.audioMode ? 'player.video' : 'player.audio'" />
                        </button>
                        <!-- the native player's own audio-only mode -->
                        <router-link
                            v-if="!useYoutubeEmbed"
                            :to="toggleListenUrl"
                            :aria-label="(isListening ? 'Watch ' : 'Listen to ') + video.title"
                            :title="(isListening ? 'Watch ' : 'Listen to ') + video.title"
                            class="btn btn-icon shrink-0"
                        >
                            <i-fa6-solid-tv v-if="isListening" />
                            <i-fa6-solid-headphones v-else />
                        </router-link>
                        <a
                            :href="youtubeAppHref"
                            target="_blank"
                            rel="noopener"
                            class="btn shrink-0"
                            @click="embed?.pause()"
                        >
                            <i-fa6-brands-youtube />
                            <span v-t="'actions.open_in_youtube'" />
                        </a>
                        <WatchOnButton
                            v-if="video.lbryId && !useYoutubeEmbed"
                            :link="`https://odysee.com/${video.lbryId}`"
                            platform="Odysee"
                        />
                        <button
                            v-if="!useYoutubeEmbed"
                            class="btn btn-icon shrink-0 max-md:hidden"
                            :title="$t('actions.download_frame')"
                            @click="downloadCurrentFrame"
                        >
                            <i-fa6-solid-download />
                        </button>
                    </div>
                    <PlaylistAddModal
                        v-if="showModal"
                        :video-id="getVideoId()"
                        :video-info="video"
                        @close="showModal = !showModal"
                    />
                    <ShareModal
                        v-if="showShareModal"
                        :video-id="getVideoId()"
                        :current-time="currentTime"
                        :playlist-id="playlistId"
                        :playlist-index="index"
                        @close="showShareModal = !showShareModal"
                    />
                </div>

                <!-- description -->
                <div
                    class="mt-4 card text-sm"
                    :class="{ 'cursor-pointer hover:bg-(--surface-hover)': !showDesc }"
                    @click="showDesc = true"
                >
                    <div class="flex flex-wrap gap-x-2 font-semibold">
                        <span v-t="{ path: 'video.views', args: { views: addCommas(video.views) } }" />
                        <span :title="new Date(video.uploadDate).toLocaleString()" v-text="uploadDate" />
                        <span
                            v-if="sponsors?.segments?.length"
                            class="font-normal text-muted"
                            v-text="`· ${$t('video.sponsor_segments')}: ${sponsors.segments.length}`"
                        />
                    </div>
                    <div
                        v-for="metaInfo in showDesc ? (video?.metaInfo ?? []) : []"
                        :key="metaInfo.title"
                        class="mt-2 rounded-lg bg-(--surface) px-3 py-2"
                    >
                        <span>{{ metaInfo.description ?? metaInfo.title }}</span>
                        <a
                            v-for="(link, linkIndex) in metaInfo.urls"
                            :key="linkIndex"
                            :href="link"
                            class="ml-1 underline"
                            >{{ metaInfo.urlTexts[linkIndex] }}</a
                        >
                    </div>
                    <!-- eslint-disable vue/no-v-html -->
                    <div
                        class="mt-2 leading-relaxed wrap-break-word whitespace-pre-line [&_a]:text-sky-600 dark:[&_a]:text-sky-400"
                        :class="{ 'line-clamp-1': !showDesc }"
                        v-html="purifiedDescription"
                    />
                    <!-- eslint-enable vue/no-v-html -->
                    <template v-if="showDesc">
                        <div class="mt-4 grid gap-0.5 text-muted">
                            <div v-if="video.category" v-text="`${$t('video.category')}: ${video.category}`" />
                            <div v-text="`${$t('video.license')}: ${video.license}`" />
                            <div class="capitalize" v-text="`${$t('video.visibility')}: ${video.visibility}`" />
                        </div>
                        <div v-if="video.tags?.length" class="mt-3 flex flex-wrap gap-1.5">
                            <router-link
                                v-for="tag in video.tags"
                                :key="tag"
                                class="chip bg-(--surface) text-xs"
                                :to="`/results?search_query=${encodeURIComponent(tag)}`"
                                >#{{ tag }}</router-link
                            >
                        </div>
                    </template>
                    <button
                        v-t="showDesc ? 'actions.show_less' : 'actions.show_more'"
                        class="mt-2 cursor-pointer font-semibold"
                        @click.stop="showDesc = !showDesc"
                    />
                </div>

                <div v-if="isMobile && (playlist || video.chapters?.length > 0)" class="mt-4 grid grid-cols-1 gap-3">
                    <PlaylistVideos
                        v-if="playlist"
                        :playlist-id="playlistId"
                        :playlist="playlist"
                        :selected-index="index"
                        :prefer-listen="isListening"
                    />
                    <ChaptersBar
                        v-if="video.chapters?.length > 0"
                        :mobile-layout="true"
                        :chapters="video.chapters"
                        :player-position="currentTime"
                        :collapsed="!showChapters"
                        @toggle="showChapters = !showChapters"
                        @seek="navigate"
                    />
                </div>

                <!-- mobile: comments teaser (opens a sheet), then recommendations -->
                <template v-if="isMobile">
                    <button
                        v-if="!comments?.disabled"
                        type="button"
                        class="mt-4 w-full cursor-pointer card text-left hover:bg-(--surface-hover)"
                        @click="openCommentsSheet"
                    >
                        <div class="flex items-center gap-2 text-sm font-semibold">
                            {{ $t("comment.comments") }}
                            <span
                                v-if="comments?.commentCount >= 0"
                                class="font-normal text-muted"
                                v-text="numberFormat(comments.commentCount)"
                            />
                            <i-fa6-solid-chevron-down class="ml-auto text-xs text-muted" />
                        </div>
                        <div v-if="firstComment" class="mt-2 flex items-center gap-2 text-sm">
                            <UiAvatar :src="firstComment.thumbnail" :name="firstComment.author" :size="24" />
                            <span class="line-clamp-2 min-w-0" v-text="plainText(firstComment.commentText)" />
                        </div>
                        <p v-else-if="!comments" v-t="'comment.loading'" class="mt-2 text-sm text-muted" />
                    </button>
                    <p v-else v-t="'comment.disabled'" class="mt-4 text-center text-sm text-muted" />

                    <div class="mt-5 flex items-center">
                        <button
                            v-t="`actions.${showRecs ? 'minimize_recommendations' : 'show_recommendations'}`"
                            class="ml-auto btn text-muted btn-ghost"
                            @click="showRecs = !showRecs"
                        />
                    </div>
                    <div v-if="showRecs" class="mt-2 grid grid-cols-1 gap-4">
                        <ContentItem
                            v-for="related in video.relatedStreams"
                            :key="related.url"
                            :item="related"
                            :prefer-listen="isListening"
                            height="94"
                            width="168"
                        />
                    </div>

                    <Teleport to="body">
                        <Transition name="sheet">
                            <div
                                v-if="showCommentsSheet"
                                data-no-swipe
                                class="fixed inset-x-0 top-[min(56.25vw,100svh)] bottom-0 z-30 flex flex-col rounded-t-2xl border-t border-(--border) bg-(--surface) text-(--text) shadow-(--shadow)"
                            >
                                <div class="flex items-center gap-2 border-b border-(--border) py-2 pr-2 pl-4">
                                    <h2 class="text-base font-bold">
                                        {{ $t("comment.comments") }}
                                        <span
                                            v-if="comments?.commentCount >= 0"
                                            class="ml-1 font-normal text-muted"
                                            v-text="numberFormat(comments.commentCount)"
                                        />
                                    </h2>
                                    <button
                                        type="button"
                                        class="ml-auto btn btn-icon btn-ghost"
                                        :aria-label="$t('actions.close')"
                                        @click="showCommentsSheet = false"
                                    >
                                        <i-fa6-solid-xmark />
                                    </button>
                                </div>
                                <div class="flex-1 overflow-y-auto overscroll-contain px-3" @scroll="onSheetScroll">
                                    <p v-if="!comments" v-t="'comment.loading'" class="mt-8 text-center text-muted" />
                                    <CommentItem
                                        v-for="comment in comments?.comments ?? []"
                                        :key="comment.commentId"
                                        :comment="comment"
                                        :uploader="video.uploader"
                                        :uploader-avatar-url="video.uploaderAvatar"
                                        :video-id="getVideoId()"
                                    />
                                </div>
                            </div>
                        </Transition>
                    </Teleport>
                </template>

                <!-- desktop: comments -->
                <template v-else>
                    <section v-if="!comments?.disabled" class="mt-6">
                        <div class="flex items-center gap-3">
                            <h2 class="text-lg font-bold">
                                {{ $t("comment.comments") }}
                                <span
                                    v-if="comments?.commentCount >= 0"
                                    class="ml-1 font-normal text-muted"
                                    v-text="numberFormat(comments.commentCount)"
                                />
                            </h2>
                            <button
                                v-t="showComments ? 'actions.minimize_comments' : 'actions.show_comments'"
                                class="ml-auto btn text-muted btn-ghost"
                                @click="toggleCommentsVisibility"
                            />
                        </div>
                        <template v-if="showComments">
                            <p v-if="!comments" v-t="'comment.loading'" class="mt-8 text-center text-muted" />
                            <div v-else ref="commentsEl" class="mt-2">
                                <CommentItem
                                    v-for="comment in comments.comments"
                                    :key="comment.commentId"
                                    :comment="comment"
                                    :uploader="video.uploader"
                                    :uploader-avatar-url="video.uploaderAvatar"
                                    :video-id="getVideoId()"
                                />
                            </div>
                        </template>
                    </section>
                    <p v-else v-t="'comment.disabled'" class="mt-8 text-center text-muted" />
                </template>
            </div>
            <aside v-if="video && showDesktopSidebar" class="w-[402px] flex-none space-y-4">
                <ChaptersBar
                    v-if="video?.chapters?.length > 0"
                    :mobile-layout="false"
                    :chapters="video.chapters"
                    :player-position="currentTime"
                    :collapsed="!showChapters"
                    @toggle="showChapters = !showChapters"
                    @seek="navigate"
                />
                <PlaylistVideos
                    v-if="playlist"
                    :playlist-id="playlistId"
                    :playlist="playlist"
                    :selected-index="index"
                    :prefer-listen="isListening"
                />
                <div v-if="showRecs" class="grid gap-3">
                    <ContentItem
                        v-for="related in video.relatedStreams"
                        :key="related.url"
                        :item="related"
                        :prefer-listen="isListening"
                        :compact="true"
                        height="94"
                        width="168"
                    />
                </div>
            </aside>
        </div>
    </LoadingIndicatorPage>
</template>

<script setup>
import { ref, computed, watch, onMounted, onActivated, onDeactivated, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import VideoPlayer from "./VideoPlayer.vue";
import YouTubeEmbed from "./YouTubeEmbed.vue";
import ContentItem from "./ContentItem.vue";
import ErrorHandler from "./ErrorHandler.vue";
import CommentItem from "./CommentItem.vue";
import ChaptersBar from "./ChaptersBar.vue";
import PlaylistAddModal from "./PlaylistAddModal.vue";
import ShareModal from "./ShareModal.vue";
import PlaylistVideos from "./PlaylistVideos.vue";
import WatchOnButton from "./WatchOnButton.vue";
import LoadingIndicatorPage from "./LoadingIndicatorPage.vue";
import ToastComponent from "./ToastComponent.vue";
import UiCheckbox from "./ui/Checkbox.vue";
import UiAvatar from "./ui/Avatar.vue";
import { parseTimeParam } from "@/utils/Misc";
import { purifyHTML, rewriteDescription } from "@/utils/HtmlUtils";
import { fetchJson, apiUrl } from "@/composables/useApi.js";
import { getPreferenceBoolean, getPreferenceNumber, setPreference } from "@/composables/usePreferences.js";
import { fetchSponsors } from "@/composables/useSponsors.js";
import {
    player,
    embed,
    isMobileLayout,
    SPEEDS,
    openVideo,
    attachPlayer,
    setPlayerSlot,
    detachPlayer,
    releasePlayer,
    closePlayer,
    minimizePlayer,
    setAudioMode,
} from "@/composables/usePlayer.js";
import { numberFormat, addCommas } from "@/composables/useFormatting.js";
import {
    fetchSubscriptionStatus,
    toggleSubscriptionState,
    fetchDeArrowContent,
} from "@/composables/useSubscriptions.js";
import { updateWatched } from "@/composables/useMisc.js";
import { getPlaylist } from "@/composables/usePlaylists.js";

const route = useRoute();
const router = useRouter();

const videoPlayer = ref(null);
const youtubeEmbed = ref(null);
const commentsEl = ref(null);

const video = ref(null);
const playlistId = ref(null);
const playlist = ref(null);
const index = ref(null);
const sponsors = ref(null);
const selectedAutoLoop = ref(false);
const selectedAutoPlay = ref(null);
const showComments = ref(true);
const showDesc = ref(false);
const showRecs = ref(true);
const showChapters = ref(true);
const comments = ref(null);
const subscribed = ref(false);
const channelId = ref(null);
const active = ref(true);
const showModal = ref(false);
const showShareModal = ref(false);
const isMobile = isMobileLayout;
const showCommentsSheet = ref(false);
const currentTime = ref(0);
const shouldShowToast = ref(false);
let timeoutCounter = null;
const counter = ref(0);
const theaterMode = ref(false);
let loading = false;

const isListening = computed(() => {
    return getPreferenceBoolean("listen", false);
});

const selectedAutoPlayEnabled = computed(() => {
    return Number(selectedAutoPlay.value) >= 1;
});

const showDesktopSidebar = computed(() => {
    return (
        !isMobile.value &&
        (showRecs.value || Boolean(playlist.value) || (video.value?.chapters?.length > 0 && showChapters.value))
    );
});

const toggleListenUrl = computed(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("listen", isListening.value ? "0" : "1");
    url.searchParams.set("t", Math.floor(currentTime.value));
    return url.pathname + url.search;
});

const isEmbed = computed(() => {
    return String(route.path).indexOf("/embed/") == 0;
});

const useYoutubeEmbed = computed(() => {
    return getPreferenceBoolean("youtubeNoCookieEmbed", true);
});

// The embed lives in GlobalPlayer (so it can continue in the mini player); the
// /embed/ route and the native player still render their own player here.
const usesGlobalPlayer = computed(() => useYoutubeEmbed.value && !isEmbed.value);

const owner = { onEnded: () => onVideoEnded(), next: () => navigateNext() };
let slotEl = null;

const dragFade = computed(() =>
    isMobile.value && player.dragOffset > 0 ? { opacity: Math.max(0.2, 1 - player.dragOffset / 300) } : null,
);

const firstComment = computed(() => comments.value?.comments?.[0]);

const embedStartTime = computed(() => {
    return parseTimeParam(route.query.t) || 0;
});

const uploadDate = computed(() => {
    return new Date(video.value.uploadDate).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
});

const defaultCounter = computed(() => {
    return getPreferenceNumber("autoPlayNextCountdown", 5);
});

const purifiedDescription = computed(() => {
    return purifyHTML(video.value.description);
});

const youtubeAppHref = computed(() => {
    let link = `https://www.youtube.com/watch?v=${getVideoId()}`;
    if (currentTime.value >= 1) link += `&t=${Math.floor(currentTime.value)}s`;
    if (playlistId.value) link += `&list=${playlistId.value}`;
    return link;
});

function fetchVideo() {
    return fetchJson(apiUrl() + "/streams/" + getVideoId());
}

function toggleCommentsVisibility() {
    showComments.value = !showComments.value;
    if (showComments.value && comments.value === null) {
        fetchCommentsData();
    }
}

function fetchCommentsData() {
    return fetchJson(apiUrl() + "/comments/" + getVideoId());
}

async function getVideoData() {
    await fetchVideo()
        .then(data => {
            video.value = data;
            video.value.id = getVideoId();
        })
        .then(() => {
            if (!video.value.error) {
                document.title = video.value.title + " - Piped";
                channelId.value = video.value.uploaderUrl.split("/")[2];
                if (!isEmbed.value) fetchSubscribedStatus();

                const parser = new DOMParser();
                const xmlDoc = parser.parseFromString(video.value.description, "text/html");
                xmlDoc.querySelectorAll("a").forEach(elem => {
                    if (!elem.innerText.match(/(?:[\d]{1,2}:)?(?:[\d]{1,2}):(?:[\d]{1,2})/))
                        elem.outerHTML = elem.getAttribute("href");
                });
                xmlDoc.querySelectorAll("br").forEach(elem => (elem.outerHTML = "\n"));
                video.value.description = rewriteDescription(xmlDoc.querySelector("body").innerHTML);
                updateWatched(video.value.relatedStreams);

                fetchDeArrowContent(video.value.relatedStreams);
            }
        });
}

async function getPlaylistData() {
    if (playlistId.value) {
        playlist.value = await getPlaylist(playlistId.value);
        await fetchPlaylistPages().then(() => {
            if (!(index.value >= 0)) {
                for (let i = 0; i < playlist.value.relatedStreams.length; i++)
                    if (playlist.value.relatedStreams[i].url.substr(-11) == getVideoId()) {
                        index.value = i + 1;
                        router.replace({
                            query: { ...route.query, index: index.value },
                        });
                        break;
                    }
            }
        });
        await fetchPlaylistPages();
    }
}

async function fetchPlaylistPages() {
    if (playlist.value.nextpage) {
        await fetchJson(apiUrl() + "/nextpage/playlists/" + playlistId.value, {
            nextpage: playlist.value.nextpage,
        }).then(json => {
            playlist.value.relatedStreams.push(...json.relatedStreams);
            playlist.value.nextpage = json.nextpage;
            fetchDeArrowContent(json.relatedStreams);
        });
        await fetchPlaylistPages();
    }
}

async function getSponsors() {
    fetchSponsors(getVideoId()).then(data => (sponsors.value = data));
}

async function getComments() {
    comments.value = await fetchCommentsData();
}

async function fetchSubscribedStatus() {
    if (!channelId.value) return;
    subscribed.value = await fetchSubscriptionStatus(channelId.value);
}

function subscribeHandler() {
    toggleSubscriptionState(channelId.value, subscribed.value).then(success => {
        if (success) subscribed.value = !subscribed.value;
    });
}

function handleClick(event) {
    if (!event || !event.target) return;
    if (!event.target.matches("a[href]")) return;
    const target = event.target;
    if (!target.getAttribute("href")) return;
    if (handleTimestampLinks(target)) {
        event.preventDefault();
    }
}

function handleTimestampLinks(target) {
    try {
        const url = new URL(target.getAttribute("href"), document.baseURI);
        if (url.searchParams.size > 2 || url.searchParams.get("v") !== getVideoId() || !url.searchParams.has("t")) {
            return false;
        }
        const time = parseTimeParam(url.searchParams.get("t"));
        if (time) {
            navigate(time);
        }
        return true;
    } catch (e) {
        console.error(e);
    }
    return false;
}

function loadMoreComments() {
    if (loading || !comments.value || !comments.value.nextpage) return;
    loading = true;
    fetchJson(apiUrl() + "/nextpage/comments/" + getVideoId(), {
        nextpage: comments.value.nextpage,
    })
        .then(json => {
            comments.value.nextpage = json.nextpage;
            comments.value.comments = comments.value.comments.concat(json.comments);
        })
        .finally(() => (loading = false));
}

function handleScroll() {
    // On phones comments live in the sheet, which loads more on its own scroll.
    if (isMobile.value || !commentsEl.value) return;
    if (window.innerHeight + window.scrollY >= commentsEl.value.offsetHeight - window.innerHeight) loadMoreComments();
}

function onSheetScroll(event) {
    const el = event.target;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 800) loadMoreComments();
}

function openCommentsSheet() {
    showCommentsSheet.value = true;
    if (comments.value === null) getComments();
}

function plainText(html) {
    return new DOMParser().parseFromString(html ?? "", "text/html").body.textContent;
}

function toggleTheaterMode() {
    theaterMode.value = !theaterMode.value;
    setPreference("theaterMode", theaterMode.value);
}

function setSlot(el) {
    slotEl = el;
    setPlayerSlot(owner, el);
}

// Hands the shared player this page's video and placeholder.
function takePlayer() {
    if (isEmbed.value) return;
    if (!usesGlobalPlayer.value) {
        closePlayer();
        return;
    }
    // The "Audio only" preference (or ?listen=1) opens new videos in the audio player.
    if (isListening.value && player.videoId !== getVideoId()) player.audioMode = true;
    openVideo({ videoId: getVideoId(), startTime: embedStartTime.value, watchUrl: route.fullPath });
    attachPlayer(owner, slotEl);
    syncPlayer();
}

function syncPlayer() {
    if (player.owner !== owner) return;
    // The route is global: while cached in <keep-alive> it may be another page's.
    if (getVideoId() === player.videoId) player.watchUrl = route.fullPath;
    player.loop = selectedAutoLoop.value;
    player.sponsors = sponsors.value;
    if (video.value && !video.value.error) {
        player.title = video.value.title;
        player.uploader = video.value.uploader;
        player.thumbnail = video.value.thumbnailUrl;
        player.related = video.value.relatedStreams ?? [];
        player.streams = video.value;
    }
    player.playlist = playlist.value?.relatedStreams
        ? { id: playlistId.value, items: playlist.value.relatedStreams, index: index.value }
        : null;
}

watch([selectedAutoLoop, sponsors, video, playlist, index, () => route.fullPath], syncPlayer);

watch(
    () => player.currentTime,
    time => {
        if (player.owner === owner) currentTime.value = time;
    },
);

function getVideoId() {
    if (route.query.video_ids) {
        const videos_list = route.query.video_ids.split(",");
        index.value = Number(route.query.index ?? 0);
        return videos_list[index.value];
    }

    return route.query.v || route.params.v;
}

function navigate(time) {
    if (usesGlobalPlayer.value) embed.value?.seek(time);
    else if (useYoutubeEmbed.value) youtubeEmbed.value?.seek(time);
    else videoPlayer.value?.seek(time);
}

function onTimeUpdate(time) {
    currentTime.value = time;
}

function onVideoEnded() {
    if (
        !selectedAutoLoop.value &&
        ((selectedAutoPlay.value >= 1 && playlist.value?.relatedStreams?.length > index.value) ||
            (selectedAutoPlay.value >= 2 && video.value.relatedStreams.length > 0))
    ) {
        showToast();
    }
}

function showToast() {
    counter.value = defaultCounter.value;
    // Timers are throttled in hidden pages, so a countdown could take minutes.
    if (counter.value < 1 || document.hidden) {
        navigateNext();
        return;
    }
    if (timeoutCounter) clearInterval(timeoutCounter);
    timeoutCounter = setInterval(() => {
        counter.value--;
        if (counter.value === 0) {
            dismiss();
            navigateNext();
        }
    }, 1000);
    shouldShowToast.value = true;
}

function dismiss() {
    clearInterval(timeoutCounter);
    shouldShowToast.value = false;
}

function navigateNext() {
    const params = route.query;
    const video_ids = route.query.video_ids?.split(",") ?? [];
    let url;
    if (playlist.value) {
        url = playlist.value?.relatedStreams?.[index.value]?.url ?? video.value.relatedStreams[0].url;
    } else if (video_ids.length > index.value + 1) {
        url = `${route.path}?index=${index.value + 1}`;
    } else {
        url = video.value.relatedStreams[0].url;
    }
    const searchParams = new URLSearchParams();
    for (var param in params)
        switch (param) {
            case "v":
            case "t":
                break;
            case "index":
                if (playlist.value && index.value < playlist.value.relatedStreams.length)
                    searchParams.set("index", index.value + 1);
                break;
            case "list":
                if (index.value < playlist.value.relatedStreams.length) searchParams.set("list", params.list);
                break;
            default:
                searchParams.set(param, params[param]);
                break;
        }
    const fullScreen = useYoutubeEmbed.value
        ? Boolean(document.fullscreenElement)
        : videoPlayer.value?.isFullScreenEnabled?.();
    searchParams.set("fullscreen", fullScreen);
    const paramStr = searchParams.toString();
    if (paramStr.length > 0) url += "&" + paramStr;
    router.push(url);
}

function downloadCurrentFrame() {
    const videoEl = document.querySelector("video");
    const canvas = document.createElement("canvas");
    canvas.width = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;

    const context = canvas.getContext("2d");
    context.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

    let link = document.createElement("a");
    const ct = Math.round(videoEl.currentTime * 1000) / 1000;
    link.download = `${video.value.title}_${ct}s.png`;
    link.href = canvas.toDataURL();
    link.click();
}

onMounted(() => {
    getVideoData().then(() => {
        (async () => {
            const videoId = getVideoId();
            if (window.db && getPreferenceBoolean("watchHistory", false) && !video.value.error) {
                var tx = window.db.transaction("watch_history", "readwrite");
                var store = tx.objectStore("watch_history");
                var request = store.get(videoId);
                request.onsuccess = function (event) {
                    var vid = event.target.result;
                    if (vid) {
                        vid.watchedAt = Date.now();
                    } else {
                        vid = {
                            videoId: videoId,
                            title: video.value.title,
                            duration: video.value.duration,
                            thumbnail: video.value.thumbnailUrl,
                            uploaderUrl: video.value.uploaderUrl,
                            uploaderName: video.value.uploader,
                            watchedAt: Date.now(),
                        };
                    }
                    store.put(vid);
                };
            }
        })();
        if (active.value && !useYoutubeEmbed.value && videoPlayer.value) videoPlayer.value.loadVideo();
    });
    playlistId.value = route.query.list;
    index.value = Number(route.query.index);
    getPlaylistData();
    getSponsors();
    if (!isEmbed.value && showComments.value) getComments();
    if (isEmbed.value) document.querySelector("html").style.overflow = "hidden";
    window.addEventListener("click", handleClick);
});

onActivated(() => {
    active.value = true;
    theaterMode.value = getPreferenceBoolean("theaterMode", window.innerWidth < (window.innerHeight * 4) / 3 + 467);
    selectedAutoPlay.value = getPreferenceNumber("autoplay", 1);
    showComments.value = !getPreferenceBoolean("minimizeComments", false);
    showDesc.value = !getPreferenceBoolean("minimizeDescription", true);
    showRecs.value = !getPreferenceBoolean("minimizeRecommendations", false);
    showChapters.value = !getPreferenceBoolean("minimizeChapters", false);
    if (video.value?.duration) {
        document.title = video.value.title + " - Piped";
        if (!useYoutubeEmbed.value && videoPlayer.value) videoPlayer.value.loadVideo();
    }
    window.addEventListener("scroll", handleScroll);
    takePlayer();
});

onDeactivated(() => {
    active.value = false;
    window.removeEventListener("scroll", handleScroll);
    dismiss();
    showCommentsSheet.value = false;
    detachPlayer(owner);
});

onUnmounted(() => {
    window.removeEventListener("scroll", handleScroll);
    window.removeEventListener("click", handleClick);
    dismiss();
    releasePlayer(owner);
});
</script>

<style>
.sheet-enter-active,
.sheet-leave-active {
    transition: transform 0.25s ease;
}
.sheet-enter-from,
.sheet-leave-to {
    transform: translateY(100%);
}

.v-enter-from,
.v-leave-to {
    opacity: 0;
    transform: translateX(100%) scale(0.5);
}
</style>
