<template>
    <img
        v-if="src && !failed"
        loading="lazy"
        :src="src"
        :alt="name"
        class="shrink-0 rounded-full bg-(--surface-muted) object-cover"
        :width="size"
        :height="size"
        :style="{ width: `${size}px`, height: `${size}px` }"
        @error="failed = true"
    />
    <!-- The Piped API often returns no avatar (e.g. for commenters), so fall back to an initial. -->
    <span
        v-else
        aria-hidden="true"
        class="flex shrink-0 items-center justify-center rounded-full font-semibold text-white uppercase select-none"
        :style="{
            width: `${size}px`,
            height: `${size}px`,
            fontSize: `${Math.round(size * 0.42)}px`,
            backgroundColor: color,
        }"
        v-text="initial"
    />
</template>

<script setup>
import { ref, computed, watch } from "vue";

defineOptions({
    name: "UiAvatar",
});

const props = defineProps({
    src: { type: String, default: null },
    name: { type: String, default: "" },
    size: { type: Number, default: 40 },
});

const failed = ref(false);
watch(
    () => props.src,
    () => (failed.value = false),
);

const cleanName = computed(() => (props.name ?? "").replace(/^@/, "").trim());

const initial = computed(() => Array.from(cleanName.value)[0] ?? "?");

// Stable, muted colour per name so the same commenter always looks the same.
const color = computed(() => {
    let hash = 0;
    for (const char of cleanName.value) hash = (hash * 31 + char.codePointAt(0)) | 0;
    return `hsl(${Math.abs(hash) % 360} 45% 45%)`;
});
</script>
