<template>
    <div v-if="text" class="py-0.5 leading-relaxed whitespace-pre-wrap [&_a]:text-sky-600 dark:[&_a]:text-sky-400">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="showFullText" class="wrap-anywhere" v-html="fullText()" />
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-else v-html="collapsedText()" />
        <span v-if="text.length > visibleLimit && !showFullText">...</span>
        <button
            v-if="text.length > visibleLimit"
            class="mt-1 block cursor-pointer text-sm font-medium whitespace-normal text-muted hover:text-(--text)"
            @click="showFullText = !showFullText"
        >
            {{ showFullText ? $t("actions.show_less") : $t("actions.show_more") }}
        </button>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { purifyHTML, rewriteDescription } from "@/utils/HtmlUtils";

const props = defineProps({
    text: {
        type: String,
        default: null,
    },
    visibleLimit: {
        type: Number,
        default: 100,
    },
});

const showFullText = ref(false);

function fullText() {
    return purifyHTML(rewriteDescription(props.text));
}

function collapsedText() {
    return purifyHTML(rewriteDescription(props.text.slice(0, props.visibleLimit)));
}
</script>
