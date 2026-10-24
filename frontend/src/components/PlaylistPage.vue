<template>
    <ErrorHandler v-if="playlist && playlist.error" :message="playlist.message" :error="playlist.error" />

    <LoadingIndicatorPage v-show="!playlist?.error" :show-content="playlist != null">
        <div class="mt-2 flex flex-col gap-4 md:flex-row md:items-end">
            <div class="min-w-0 flex-1">
                <h1 class="text-2xl font-bold sm:text-3xl" v-text="playlist.name" />
                <router-link
                    v-if="playlist.uploader"
                    class="mt-3 flex w-fit items-center gap-2 text-sm font-semibold"
                    :to="playlist.uploaderUrl || '/'"
                >
                    <UiAvatar :src="playlist.uploaderAvatar" :name="playlist.uploader" :size="28" />
                    <span v-text="playlist.uploader" />
                </router-link>
                <div
                    class="mt-1 text-sm text-muted"
                    v-text="
                        `${playlist.videos} ${$t('video.videos')} · ${timeFormat(totalDuration)}${
                            playlist.nextpage ? '+' : ''
                        }`
                    "
                />
                <CollapsableText
                    v-if="playlist?.description"
                    :text="playlist.description"
                    class="mt-1 max-w-3xl text-sm text-muted"
                />
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <router-link
                    v-if="playlist.relatedStreams?.length"
                    class="btn btn-primary"
                    :to="{
                        path: '/watch',
                        query: { v: playlist.relatedStreams[0].url.substr(-11), list: $route.query.list, index: 1 },
                    }"
                >
                    <i-fa6-solid-play class="text-xs" />
                    <span v-t="'actions.play_all'" />
                </router-link>
                <button v-if="!isPipedPlaylist" class="btn" @click="bookmarkPlaylist">
                    <i-fa6-solid-bookmark />
                    {{ $t(`actions.${isBookmarked ? "playlist_bookmarked" : "bookmark_playlist"}`) }}
                </button>
                <button v-if="authenticated && !isPipedPlaylist" class="btn" @click="clonePlaylist">
                    <i-fa6-solid-clone />
                    {{ $t("actions.clone_playlist") }}
                </button>
                <button class="btn" @click="downloadPlaylistAsTxt">
                    <i-fa6-solid-download />
                    {{ $t("actions.download_as_txt") }}
                </button>
                <a class="btn btn-icon" :href="getRssUrl" :aria-label="$t('actions.playlist_rss_feed')">
                    <i-fa6-solid-rss />
                </a>
                <WatchOnButton :link="`https://www.youtube.com/playlist?list=${$route.query.list}`" />
            </div>
        </div>

        <hr class="my-5" />

        <p
            v-if="!playlist.relatedStreams?.length && playlist.videos > 0"
            v-t="'info.playlist_videos_unavailable'"
            class="py-12 text-center text-muted"
        />

        <div class="video-grid">
            <VideoItem
                v-for="(video, index) in playlist.relatedStreams"
                :key="video.url"
                :item="video"
                :index="index"
                :playlist-id="$route.query.list"
                :admin="admin"
                height="94"
                width="168"
                @remove="removeVideo(index)"
            />
        </div>
    </LoadingIndicatorPage>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onDeactivated } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import ErrorHandler from "./ErrorHandler.vue";
import UiAvatar from "./ui/Avatar.vue";
import LoadingIndicatorPage from "./LoadingIndicatorPage.vue";
import CollapsableText from "./CollapsableText.vue";
import VideoItem from "./VideoItem.vue";
import WatchOnButton from "./WatchOnButton.vue";
import { fetchJson, authApiUrl, getAuthToken, isAuthenticated } from "@/composables/useApi.js";
import { getPlaylists } from "@/composables/usePlaylists.js";
import { getPlaylist } from "@/composables/usePlaylists.js";
import { updateWatched, download } from "@/composables/useMisc.js";
import { fetchDeArrowContent } from "@/composables/useSubscriptions.js";
import { timeFormat } from "@/composables/useFormatting.js";

const route = useRoute();
const { t } = useI18n();

const playlist = ref(null);
const totalDuration = ref(0);
const admin = ref(false);
const isBookmarked = ref(false);
let loading = false;

const getRssUrl = computed(() => {
    return authApiUrl() + "/rss/playlists/" + route.query.list;
});

const isPipedPlaylist = computed(() => {
    return /[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}/.test(route.query.list);
});

function updateTitle() {
    document.title = playlist.value.name + " - Piped";
}

function updateTotalDuration() {
    totalDuration.value = playlist.value.relatedStreams.map(video => video.duration).reduce((a, b) => a + b);
}

async function getPlaylistData() {
    getPlaylist(route.query.list)
        .then(data => (playlist.value = data))
        .then(() => {
            updateTitle();
            updateTotalDuration();
            updateWatched(playlist.value.relatedStreams);
            fetchDeArrowContent(playlist.value.relatedStreams);
        });
}

function handleScroll() {
    if (loading || !playlist.value || !playlist.value.nextpage) return;
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - window.innerHeight) {
        loading = true;
        fetchJson(authApiUrl() + "/nextpage/playlists/" + route.query.list, {
            nextpage: playlist.value.nextpage,
        }).then(json => {
            playlist.value.nextpage = json.nextpage;
            loading = false;
            playlist.value.relatedStreams.push(...json.relatedStreams);
            updateTotalDuration();
            fetchDeArrowContent(json.relatedStreams);
        });
    }
}

function removeVideo(index) {
    playlist.value.relatedStreams.splice(index, 1);
}

async function clonePlaylist() {
    fetchJson(authApiUrl() + "/import/playlist", null, {
        method: "POST",
        headers: {
            Authorization: getAuthToken(),
        },
        body: JSON.stringify({
            playlistId: route.query.list,
        }),
    }).then(resp => {
        if (!resp.error) {
            alert(t("actions.clone_playlist_success"));
        } else alert(resp.error);
    });
}

function downloadPlaylistAsTxt() {
    const data = playlist.value.relatedStreams
        .map(video => {
            return "https://piped.video" + video.url;
        })
        .join("\n");
    download(data, playlist.value.name + ".txt", "text/plain");
}

async function bookmarkPlaylist() {
    if (!playlist.value) return;

    if (isBookmarked.value) {
        removePlaylistBookmark();
        return;
    }

    if (window.db) {
        const playlistId = route.query.list;
        var tx = window.db.transaction("playlist_bookmarks", "readwrite");
        var store = tx.objectStore("playlist_bookmarks");
        store.put({
            playlistId: playlistId,
            name: playlist.value.name,
            uploader: playlist.value.uploader,
            uploaderUrl: playlist.value.uploaderUrl,
            thumbnail: playlist.value.thumbnailUrl,
            uploaderAvatar: playlist.value.uploaderAvatar,
            videos: playlist.value.videos,
        });
        isBookmarked.value = true;
    }
}

async function removePlaylistBookmark() {
    var tx = window.db.transaction("playlist_bookmarks", "readwrite");
    var store = tx.objectStore("playlist_bookmarks");
    store.delete(route.query.list);
    isBookmarked.value = false;
}

async function checkPlaylistBookmarked() {
    const playlistId = route.query.list;
    var tx = window.db.transaction("playlist_bookmarks", "readwrite");
    var store = tx.objectStore("playlist_bookmarks");
    var req = store.openCursor(playlistId);
    req.onsuccess = function (e) {
        var cursor = e.target.result;
        isBookmarked.value = cursor ? true : false;
    };
}

onMounted(() => {
    const playlistId = route.query.list;
    if (isAuthenticated() && playlistId?.length == 36)
        getPlaylists().then(json => {
            if (json.error) alert(json.error);
            else if (json.some(pl => pl.id === playlistId)) admin.value = true;
        });
    else if (playlistId?.startsWith("local")) admin.value = true;
    checkPlaylistBookmarked();
});

onActivated(() => {
    getPlaylistData();
    window.addEventListener("scroll", handleScroll);
    if (playlist.value) updateTitle();
});

onDeactivated(() => {
    window.removeEventListener("scroll", handleScroll);
});
</script>
