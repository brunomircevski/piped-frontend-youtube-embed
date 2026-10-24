<template>
    <!-- desktop view -->
    <div
        v-if="!mobileLayout"
        class="flex max-h-[60vh] flex-col overflow-hidden rounded-xl border border-(--border) max-lg:hidden"
    >
        <button
            type="button"
            class="flex w-full cursor-pointer items-center gap-2 px-4 py-3 text-left hover:bg-(--surface-hover)"
            :class="{ 'border-b border-(--border)': !collapsed }"
            :aria-expanded="!collapsed"
            @click="$emit('toggle')"
        >
            <h2 class="text-base! font-semibold" aria-label="chapters">
                {{ $t("video.chapters") }}
                <span class="ml-1 font-normal text-muted">{{ chapters.length }}</span>
            </h2>
            <i-fa6-solid-chevron-down
                class="ml-auto text-xs text-muted transition-transform"
                :class="{ 'rotate-180': !collapsed }"
            />
        </button>
        <div v-if="!collapsed" class="overflow-y-auto p-1.5">
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

    <div v-else>
        <button
            type="button"
            class="flex w-full cursor-pointer items-center gap-2 py-1 text-left"
            :aria-expanded="!collapsed"
            @click="$emit('toggle')"
        >
            <h2 class="text-sm! font-semibold" aria-label="chapters">
                {{ $t("video.chapters") }}
                <span class="ml-1 font-normal text-muted">{{ chapters.length }}</span>
            </h2>
            <span v-if="collapsed && currentChapter" class="min-w-0 truncate text-sm text-muted">
                · {{ currentChapter.title }}
            </span>
            <i-fa6-solid-chevron-down
                class="ml-auto shrink-0 text-xs text-muted transition-transform"
                :class="{ 'rotate-180': !collapsed }"
            />
        </button>

        <template v-if="!collapsed">
            <!-- mobile vertical view -->
            <div
                v-if="getPreferenceString('mobileChapterLayout', 'Horizontal') == 'Vertical'"
                class="mt-1 flex max-h-64 flex-col overflow-y-auto"
            >
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
                        <span
                            class="text-xs font-medium text-sky-600 dark:text-sky-400"
                            v-text="timeFormat(chapter.start)"
                        />
                    </div>
                </div>
            </div>
            <!-- mobile Horizontal view -->
            <div v-else class="mt-1 flex gap-2 overflow-x-auto pb-2">
                <div
                    v-for="(chapter, index) in chapters"
                    :key="chapter.start"
                    class="w-36 flex-none cursor-pointer rounded-xl p-1.5"
                    :class="isCurrentChapter(index) ? 'bg-(--surface-muted)' : ''"
                    @click="$emit('seek', chapter.start)"
                >
                    <img
                        class="aspect-video w-full rounded-lg object-cover"
                        :src="chapter.image"
                        :alt="chapter.title"
                    />
                    <div class="mt-1 px-0.5">
                        <span class="line-clamp-2 text-xs/tight" :title="chapter.title" v-text="chapter.title" />
                        <span
                            class="text-xs font-medium text-sky-600 dark:text-sky-400"
                            v-text="timeFormat(chapter.start)"
                        />
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<script setup>
import { computed } from "vue";
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
    collapsed: Boolean,
});

const isCurrentChapter = index => {
    return (
        props.playerPosition >= props.chapters[index].start &&
        props.playerPosition < (props.chapters[index + 1]?.start ?? Infinity)
    );
};

const currentChapter = computed(() => props.chapters.find((_, index) => isCurrentChapter(index)));

defineEmits(["seek", "toggle"]);
</script>

<style scoped>
@reference "../app.css";

::-webkit-scrollbar {
    height: 5px;
}
</style>
