<template>
    <!-- compact horizontal card (watch page sidebar) -->
    <div v-if="showVideo && compact" class="group flex gap-2">
        <router-link :to="watchRoute" class="w-[168px] shrink-0">
            <VideoThumbnail :item="item" small />
        </router-link>
        <div class="min-w-0 flex-1">
            <router-link :to="watchRoute">
                <p class="line-clamp-2 text-sm/snug font-semibold" :title="title" v-text="title" />
            </router-link>
            <router-link
                v-if="item.uploaderUrl && item.uploaderName"
                class="mt-1 flex items-center gap-1 text-xs text-muted hover:text-(--text)"
                :to="item.uploaderUrl"
                :title="item.uploaderName"
            >
                <span class="truncate" v-text="item.uploaderName" />
                <i-fa6-solid-circle-check v-if="item.uploaderVerified" class="shrink-0 text-[10px]" />
            </router-link>
            <div class="text-xs text-muted">
                <span v-if="item.views >= 0" v-t="{ path: 'video.views', args: { views: numberFormat(item.views) } }" />
                <span v-if="item.uploaded > 0" v-text="` • ${timeAgo(item.uploaded)}`" />
                <span v-else-if="item.uploadedDate" v-text="` • ${item.uploadedDate}`" />
            </div>
        </div>
    </div>
    <div v-else-if="showVideo" class="group flex flex-col">
        <router-link
            class="block w-full"
            :to="{
                path: '/watch',
                query: {
                    v: item.url.substr(-11),
                    ...(playlistId && { list: playlistId }),
                    ...(index >= 0 && { index: index + 1 }),
                    ...(preferListen && { listen: 1 }),
                },
            }"
        >
            <VideoThumbnail :item="item" />

            <div>
                <p
                    class="line-clamp-2 pt-3 text-[0.9375rem] leading-snug font-semibold"
                    :title="title"
                    v-text="title"
                />
            </div>
        </router-link>

        <div class="relative flex items-start gap-3 pt-1.5">
            <router-link :to="item.uploaderUrl">
                <img
                    v-if="item.uploaderAvatar"
                    loading="lazy"
                    :src="item.uploaderAvatar"
                    class="mt-0.5 size-9 shrink-0 rounded-full bg-(--surface-muted)"
                    width="68"
                    height="68"
                />
            </router-link>

            <div class="min-w-0 flex-1">
                <router-link
                    v-if="item.uploaderUrl && item.uploaderName && !hideChannel"
                    class="flex max-w-full items-center gap-1 text-sm text-muted hover:text-(--text)"
                    :to="item.uploaderUrl"
                    :title="item.uploaderName"
                >
                    <span class="truncate" v-text="item.uploaderName" />
                    <i-fa6-solid-circle-check v-if="item.uploaderVerified" class="shrink-0 text-xs" />
                </router-link>

                <div v-if="item.views >= 0 || item.uploadedDate" class="truncate text-sm text-muted">
                    <span
                        v-if="item.views >= 0"
                        v-t="{ path: 'video.views', args: { views: numberFormat(item.views) } }"
                        class="after:mx-1 after:content-['•']"
                    />
                    <span
                        v-if="item.uploaded > 0"
                        :title="new Date(item.uploaded).toLocaleString()"
                        v-text="timeAgo(item.uploaded)"
                    />
                    <span v-else-if="item.uploadedDate" v-text="item.uploadedDate" />
                </div>
            </div>

            <div
                class="flex shrink-0 items-center gap-0.5 text-sm text-muted transition-opacity *:flex *:size-8 *:items-center *:justify-center *:rounded-full *:hover:bg-(--surface-muted) *:hover:text-(--text) [@media(hover:hover)]:absolute [@media(hover:hover)]:top-1 [@media(hover:hover)]:right-0 [@media(hover:hover)]:rounded-full [@media(hover:hover)]:bg-(--surface) [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:shadow-sm [@media(hover:hover)]:group-hover:opacity-100 [@media(hover:hover)]:focus-within:opacity-100"
            >
                <router-link
                    :to="{
                        path: '/watch',
                        query: {
                            v: item.url.substr(-11),
                            ...(playlistId && { list: playlistId }),
                            ...(index >= 0 && { index: index + 1 }),
                            ...(!preferListen && { listen: 1 }),
                        },
                    }"
                    :aria-label="preferListen ? title : 'Listen to ' + title"
                    :title="preferListen ? title : 'Listen to ' + title"
                >
                    <i-fa6-solid-tv v-if="preferListen" />
                    <i-fa6-solid-headphones v-else />
                </router-link>
                <button :title="$t('actions.add_to_playlist')" @click="showPlaylistModal = !showPlaylistModal">
                    <i-fa6-solid-circle-plus />
                </button>
                <button :title="$t('actions.share')" @click="showShareModal = !showShareModal">
                    <i-fa6-solid-share />
                </button>
                <button
                    v-if="admin"
                    ref="removeButton"
                    :title="$t('actions.remove_from_playlist')"
                    @click="showConfirmRemove = true"
                >
                    <i-fa6-solid-circle-minus />
                </button>
                <button
                    v-if="showMarkOnWatched && isFeed"
                    ref="watchButton"
                    @click="toggleWatched(item.url.substr(-11))"
                >
                    <i-fa6-solid-eye-slash
                        v-if="item.watched && item.currentTime > item.duration * 0.9"
                        :title="$t('actions.mark_as_unwatched')"
                    />
                    <i-fa6-solid-eye v-else :title="$t('actions.mark_as_watched')" />
                </button>
                <ConfirmModal
                    v-if="showConfirmRemove"
                    :message="$t('actions.delete_playlist_video_confirm')"
                    @close="showConfirmRemove = false"
                    @confirm="removeVideo(item.url.substr(-11))"
                />
                <PlaylistAddModal
                    v-if="showPlaylistModal"
                    :video-id="item.url.substr(-11)"
                    :video-info="item"
                    @close="showPlaylistModal = false"
                />
                <ShareModal
                    v-if="showShareModal"
                    :video-id="item.url.substr(-11)"
                    :current-time="0"
                    @close="showShareModal = false"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import PlaylistAddModal from "./PlaylistAddModal.vue";
import ShareModal from "./ShareModal.vue";
import ConfirmModal from "./ConfirmModal.vue";
import VideoThumbnail from "./VideoThumbnail.vue";
import { numberFormat, timeAgo } from "@/composables/useFormatting.js";
import { getPreferenceBoolean } from "@/composables/usePreferences.js";
import { removeVideoFromPlaylist } from "@/composables/usePlaylists.js";

const props = defineProps({
    item: {
        type: Object,
        default: () => {
            return {};
        },
    },
    isFeed: {
        type: Boolean,
        default: false,
    },
    height: { type: String, default: "118" },
    width: { type: String, default: "210" },
    hideChannel: { type: Boolean, default: false },
    index: { type: Number, default: -1 },
    playlistId: { type: String, default: null },
    preferListen: { type: Boolean, default: false },
    admin: { type: Boolean, default: false },
    compact: { type: Boolean, default: false },
});

const watchRoute = computed(() => ({
    path: "/watch",
    query: {
        v: props.item.url.substr(-11),
        ...(props.playlistId && { list: props.playlistId }),
        ...(props.index >= 0 && { index: props.index + 1 }),
        ...(props.preferListen && { listen: 1 }),
    },
}));

const emit = defineEmits(["update:watched", "remove"]);

const removeButton = ref(null);
const showPlaylistModal = ref(false);
const showShareModal = ref(false);
const showVideo = ref(true);
const showConfirmRemove = ref(false);
const showMarkOnWatched = ref(false);

const title = computed(() => {
    return props.item.dearrow?.titles[0]?.title ?? props.item.title;
});

function removeVideo() {
    removeButton.value.disabled = true;
    removeVideoFromPlaylist(props.playlistId, props.index).then(json => {
        if (json.error) alert(json.error);
        else emit("remove");
    });
}

function shouldShowVideo() {
    if (!props.isFeed || !getPreferenceBoolean("hideWatched", false)) return;

    const objectStore = window.db.transaction("watch_history", "readonly").objectStore("watch_history");
    const request = objectStore.get(props.item.url.substr(-11));
    request.onsuccess = event => {
        const video = event.target.result;
        if (video && (video.currentTime ?? 0) > video.duration * 0.9) {
            showVideo.value = false;
            return;
        }
    };
}

function shouldShowMarkOnWatched() {
    showMarkOnWatched.value = getPreferenceBoolean("watchHistory", false);
}

function toggleWatched(videoId) {
    if (window.db) {
        var tx = window.db.transaction("watch_history", "readwrite");
        var store = tx.objectStore("watch_history");
        var request = store.get(videoId);
        request.onsuccess = function (event) {
            var video = event.target.result;
            if (video) {
                video.watchedAt = Date.now();
            } else {
                video = {
                    videoId: videoId,
                    title: props.item.title,
                    duration: props.item.duration,
                    thumbnail: props.item.thumbnail,
                    uploaderUrl: props.item.uploaderUrl,
                    uploaderName: props.item.uploaderName,
                    watchedAt: Date.now(),
                };
            }
            video.currentTime = props.item.currentTime < props.item.duration * 0.9 ? props.item.duration : 0;
            store.put(video);
            emit("update:watched", [props.item.url]);
            shouldShowVideo();
        };
    }
}

onMounted(() => {
    shouldShowVideo();
    shouldShowMarkOnWatched();
});
</script>
