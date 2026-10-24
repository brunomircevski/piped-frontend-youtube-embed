<template>
    <div class="rounded-t-xl border border-b-0 border-(--border) px-4 pt-3 pb-2">
        <router-link :to="{ path: '/playlist', query: { list: playlistId } }"
            ><h1 class="text-lg! font-bold hover:underline" v-text="playlist.name"
        /></router-link>
        <span class="text-xs text-muted">
            <template v-if="playlist.uploader">
                <router-link class="hover:text-(--text)" :to="playlist.uploaderUrl" :title="playlist.uploader">
                    {{ playlist.uploader }}
                </router-link>
                -
            </template>
            {{ selectedIndex }} / {{ playlist.videos }}
        </span>
    </div>
    <div ref="scrollable" class="max-h-112 overflow-y-auto rounded-b-xl border border-t-0 border-(--border) p-1.5">
        <div
            v-for="(related, index) in playlist.relatedStreams"
            :key="related.url"
            :index="index"
            :playlist-id="playlistId"
            :prefer-listen="preferListen"
        >
            <router-link
                class="flex items-center gap-1 rounded-lg p-1.5 hover:bg-(--surface-muted)"
                :class="{ 'bg-(--surface-muted)': index === selectedIndex - 1 }"
                :to="{
                    path: '/watch',
                    query: {
                        v: related.url.substr(-11),
                        ...(playlistId && { list: playlistId }),
                        ...(index >= 0 && { index: index + 1 }),
                        ...(preferListen && { listen: 1 }),
                    },
                }"
            >
                <span class="min-w-6 flex-none text-center text-xs text-muted" v-text="index + 1" />
                <div class="w-24 flex-none">
                    <VideoThumbnail :item="related" :small="true" />
                </div>

                <div class="ml-2 flex flex-col">
                    <span class="line-clamp-2 text-sm font-medium" :title="related.title" v-text="related.title" />
                    <div class="flex-1">
                        <router-link
                            v-if="related.uploaderUrl && related.uploaderName && !hideChannel"
                            class="mt-0.5 block overflow-hidden text-xs text-muted hover:text-(--text)"
                            :to="related.uploaderUrl"
                            :title="related.uploaderName"
                        >
                            <span v-text="related.uploaderName" />
                            <i-fa6-solid-check v-if="related.uploaderVerified" class="ml-1.5" />
                        </router-link>
                    </div>
                </div>
            </router-link>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from "vue";
import VideoThumbnail from "./VideoThumbnail.vue";
import { updateWatched } from "@/composables/useMisc.js";

const props = defineProps({
    playlist: {
        type: Object,
        required: true,
    },
    playlistId: {
        type: String,
        required: true,
    },
    selectedIndex: {
        type: Number,
        required: true,
    },
    preferListen: {
        type: Boolean,
        default: false,
    },
});

const scrollable = ref(null);

watch(
    () => props.playlist,
    () => {
        if (props.selectedIndex - 1 < props.playlist.relatedStreams.length)
            nextTick(() => {
                updateScroll();
            });
    },
    { deep: true },
);

function updateScroll() {
    const elems = Array.from(scrollable.value.children).filter(elm => elm.matches("div"));
    const index = props.selectedIndex - 1;
    if (index < elems.length)
        scrollable.value.scrollTop = elems[props.selectedIndex - 1].offsetTop - scrollable.value.offsetTop;
}

onMounted(() => {
    updateScroll();
    updateWatched(props.playlist.relatedStreams);
});
</script>
