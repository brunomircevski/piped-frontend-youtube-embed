<template>
    <div class="relative w-full overflow-hidden rounded-xl bg-(--surface-muted)">
        <img
            loading="lazy"
            class="aspect-video w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            :src="item.thumbnail"
            :alt="item.title"
            :class="{ 'opacity-75': item.watched }"
        />
        <!-- progress bar -->
        <div v-if="item.watched && item.duration > 0" class="absolute inset-x-0 bottom-0 h-1 bg-white/30">
            <div
                class="absolute bottom-0 left-0 h-1 bg-(--accent)"
                :style="{ width: `clamp(0%, ${(item.currentTime / item.duration) * 100}%, 100%` }"
            />
        </div>
        <!-- shorts thumbnail -->
        <span
            v-if="item.isShort"
            v-t="'video.shorts'"
            class="absolute bottom-2 left-2 rounded-md bg-(--accent) px-1.5 py-0.5 text-xs font-semibold text-white uppercase"
        />
        <span
            v-if="item.duration > 0 || (item.duration == 0 && item.isShort)"
            class="absolute right-2 bottom-2 rounded-md bg-black/80 px-1.5 py-0.5 text-xs font-medium text-white tabular-nums"
            v-text="timeFormat(item.duration)"
        />
        <i18n-t
            v-else
            keypath="video.live"
            class="absolute right-2 bottom-2 inline-flex items-center gap-1 rounded-md bg-(--accent) px-1.5 py-0.5 text-xs font-medium text-white"
            tag="div"
        >
            <i-fa6-solid-tower-broadcast class="w-3" />
        </i18n-t>
        <span
            v-if="item.watched"
            v-t="'video.watched'"
            class="absolute bottom-2.5 left-2 rounded-md bg-black/80 px-1.5 py-0.5 text-xs font-medium text-white"
        />
    </div>
</template>
<script setup>
import { timeFormat } from "@/composables/useFormatting.js";

defineProps({
    item: {
        type: Object,
        default: () => {
            return {};
        },
    },
    small: {
        type: Boolean,
        default: () => {
            return false;
        },
    },
});
</script>
