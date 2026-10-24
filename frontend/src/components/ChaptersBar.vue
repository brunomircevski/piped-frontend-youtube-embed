<template>
    <!-- desktop view -->
    <div
        v-if="!mobileLayout"
        class="flex max-h-[60vh] flex-col overflow-hidden rounded-xl border border-(--border) max-lg:hidden"
    >
        <h2 class="border-b border-(--border) px-4 py-3 text-base! font-semibold" aria-label="chapters">
            {{ $t("video.chapters") }}
            <span class="ml-1 font-normal text-muted">{{ chapters.length }}</span>
        </h2>
        <div class="overflow-y-auto p-1.5">
            <button
                v-for="(chapter, index) in chapters"
                :key="chapter.start"
                class="flex w-full cursor-pointer items-center gap-3 rounded-lg p-1.5 text-left hover:bg-(--surface-muted)"
                :class="{ 'bg-(--surface-muted)': isCurrentChapter(index) }"
                @click="$emit('seek', chapter.start)"
            >
                <img class="aspect-video w-24 shrink-0 rounded-md object-cover" :src="chapter.image" alt="" />
                <div class="flex min-w-0 flex-col gap-0.5">
                    <span class="line-clamp-2 text-sm font-medium" :title="chapter.title" v-text="chapter.title" />
                    <span
                        class="w-fit rounded-sm bg-sky-500/10 px-1.5 text-xs font-medium text-sky-600 tabular-nums dark:text-sky-400"
                        v-text="timeFormat(chapter.start)"
                    />
                </div>
            </button>
        </div>
    </div>

    <!-- mobile vertical view -->
    <div
        v-if="mobileLayout && getPreferenceString('mobileChapterLayout', 'Horizontal') == 'Vertical'"
        class="flex max-h-64 flex-col overflow-y-auto"
    >
        <h2 class="mb-1 px-1 text-sm! font-semibold" aria-label="chapters">
            {{ $t("video.chapters") }} ({{ chapters.length }})
        </h2>
        <div
            v-for="(chapter, index) in chapters"
            :key="chapter.start"
            class="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-(--surface-muted)"
            :class="{ 'bg-(--surface-muted)': isCurrentChapter(index) }"
            @click="$emit('seek', chapter.start)"
        >
            <span class="w-5 shrink-0 text-center text-xs" v-text="index + 1" />
            <img class="h-10 w-16 shrink-0 rounded-sm object-cover" :src="chapter.image" :alt="chapter.title" />
            <div class="flex min-w-0 flex-col">
                <span class="truncate text-sm" :title="chapter.title" v-text="chapter.title" />
                <span class="text-xs font-medium text-sky-600 dark:text-sky-400" v-text="timeFormat(chapter.start)" />
            </div>
        </div>
    </div>
    <!-- mobile Horizontal view -->
    <div
        v-if="getPreferenceString('mobileChapterLayout', 'Horizontal') == 'Horizontal' && mobileLayout"
        class="flex gap-2 overflow-x-auto pb-2"
    >
        <div
            v-for="(chapter, index) in chapters"
            :key="chapter.start"
            class="w-36 flex-none cursor-pointer rounded-xl p-1.5"
            :class="isCurrentChapter(index) ? 'bg-(--surface-muted)' : ''"
            @click="$emit('seek', chapter.start)"
        >
            <img class="aspect-video w-full rounded-lg object-cover" :src="chapter.image" :alt="chapter.title" />
            <div class="mt-1 px-0.5">
                <span class="line-clamp-2 text-xs/tight" :title="chapter.title" v-text="chapter.title" />
                <span class="text-xs font-medium text-sky-600 dark:text-sky-400" v-text="timeFormat(chapter.start)" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { timeFormat } from "@/composables/useFormatting.js";
import { getPreferenceString } from "@/composables/usePreferences.js";

const props = defineProps({
    chapters: {
        type: Object,
        default: () => null,
    },
    mobileLayout: {
        type: Boolean,
        default: () => true,
    },
    playerPosition: {
        type: Number,
        default: () => 0,
    },
});

const isCurrentChapter = index => {
    return (
        props.playerPosition >= props.chapters[index].start &&
        props.playerPosition < (props.chapters[index + 1]?.start ?? Infinity)
    );
};

defineEmits(["seek"]);
</script>

<style scoped>
@reference "../app.css";

::-webkit-scrollbar {
    height: 5px;
}
</style>
