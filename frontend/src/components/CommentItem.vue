<template>
    <div class="flex gap-3 py-3">
        <router-link :to="comment.commentorUrl" class="shrink-0">
            <UiAvatar :src="comment.thumbnail" :name="comment.author" :size="40" />
        </router-link>

        <div class="min-w-0 flex-1">
            <div v-if="comment.pinned" class="mb-1 flex items-center gap-1.5 text-xs text-muted">
                <i-fa6-solid-thumbtack />
                <span v-t="{ path: 'comment.pinned_by', args: { author: uploader } }" />
            </div>

            <div class="flex flex-wrap items-center gap-x-2 text-sm">
                <router-link
                    class="inline-flex items-center gap-1 font-semibold"
                    :class="comment.channelOwner ? 'rounded-full bg-(--surface-hover) px-2 py-0.5' : 'hover:underline'"
                    :to="comment.commentorUrl"
                >
                    {{ comment.author }}
                    <i-fa6-solid-circle-check v-if="comment.verified" class="text-xs text-muted" />
                </router-link>
                <span class="text-xs text-muted" v-text="comment.commentedTime" />
            </div>

            <CollapsableText :text="comment.commentText" :visible-limit="500" class="text-[0.9375rem]" />

            <div class="mt-1 flex items-center gap-4 text-sm text-muted">
                <span class="inline-flex items-center gap-1.5">
                    <i-fa6-solid-thumbs-up class="text-xs" />
                    <span v-text="numberFormat(comment.likeCount)" />
                </span>
                <span v-if="comment.hearted" class="relative inline-flex" :title="$t('actions.creator_liked')">
                    <UiAvatar :src="uploaderAvatarUrl" :name="uploader" :size="20" />
                    <i-fa6-solid-heart class="absolute -right-1.5 -bottom-1 text-[10px] text-(--accent)" />
                </span>
                <UiAvatar
                    v-else-if="comment.creatorReplied"
                    :src="uploaderAvatarUrl"
                    :name="uploader"
                    :size="20"
                    :title="$t('actions.creator_replied')"
                />
            </div>

            <button
                v-if="comment.repliesPage && (!loadingReplies || !showingReplies)"
                class="mt-1.5 -ml-3 inline-flex cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-sky-600 hover:bg-sky-500/10 dark:text-sky-400"
                @click="loadReplies"
            >
                <i-fa6-solid-chevron-down class="text-xs" />
                {{ $t("actions.reply_count", comment.replyCount) }}
            </button>
            <button
                v-if="showingReplies"
                class="mt-1.5 -ml-3 inline-flex cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-sky-600 hover:bg-sky-500/10 dark:text-sky-400"
                @click="hideReplies"
            >
                <i-fa6-solid-chevron-up class="text-xs" />
                {{ $t("actions.hide_replies") }}
            </button>
            <div v-show="showingReplies" v-if="replies">
                <div v-for="reply in replies" :key="reply.commentId" class="w-full">
                    <!-- eslint-disable-next-line vue/no-undef-components -->
                    <CommentItem
                        :comment="reply"
                        :uploader="uploader"
                        :uploader-avatar-url="uploaderAvatarUrl"
                        :video-id="videoId"
                    />
                </div>
                <button
                    v-if="nextpage"
                    class="-ml-3 inline-flex cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-sky-600 hover:bg-sky-500/10 dark:text-sky-400"
                    @click="loadReplies"
                >
                    <i-fa6-solid-turn-up class="rotate-90 text-xs" />
                    {{ $t("actions.load_more_replies") }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from "vue";
import CollapsableText from "./CollapsableText.vue";
import UiAvatar from "./ui/Avatar.vue";
import { fetchJson, apiUrl } from "@/composables/useApi.js";
import { numberFormat } from "@/composables/useFormatting.js";

const props = defineProps({
    comment: {
        type: Object,
        default: () => {
            return {};
        },
    },
    uploader: { type: String, default: null },
    uploaderAvatarUrl: { type: String, default: null },
    videoId: { type: String, default: null },
});

const loadingReplies = ref(false);
const showingReplies = ref(false);
const replies = ref([]);
const nextpage = ref(null);

async function loadReplies() {
    if (!showingReplies.value && loadingReplies.value) {
        showingReplies.value = true;
        return;
    }
    loadingReplies.value = true;
    showingReplies.value = true;
    fetchJson(apiUrl() + "/nextpage/comments/" + props.videoId, {
        nextpage: nextpage.value || props.comment.repliesPage,
    }).then(json => {
        replies.value = replies.value.concat(json.comments);
        nextpage.value = json.nextpage;
    });
}

async function hideReplies() {
    showingReplies.value = false;
}
</script>
