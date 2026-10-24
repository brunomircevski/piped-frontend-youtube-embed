<template>
    <div class="flex flex-col justify-between">
        <router-link :to="item.url" class="font-bold link">
            <div class="my-4 flex justify-center">
                <img loading="lazy" class="aspect-square w-[50%] rounded-full" :src="item.thumbnail" />
            </div>
            <p class="line-clamp-2 leading-tight">
                <span v-text="item.name" />
                <i-fa6-solid-check v-if="item.verified" class="ml-1.5" />
            </p>
        </router-link>
        <p v-if="item.description" class="line-clamp-2 pt-1 text-sm text-muted" v-text="item.description" />
        <router-link
            v-if="item.uploaderUrl"
            class="mt-1 line-clamp-1 block text-sm text-muted hover:text-(--text)"
            :to="item.uploaderUrl"
        >
            <p class="leading-tight">
                <span v-text="item.uploader" />
                <i-fa6-solid-check v-if="item.uploaderVerified" class="ml-1.5" />
            </p>
        </router-link>

        <a
            v-if="item.uploaderName"
            class="mt-1 line-clamp-1 block text-sm text-muted hover:text-(--text)"
            v-text="item.uploaderName"
        />
        <template v-if="item.videos >= 0">
            <strong class="mt-1 text-sm" v-text="`${item.videos} ${$t('video.videos')}`" />
        </template>

        <button
            v-if="subscribed != null"
            class="mt-2 btn w-max"
            @click="subscribeHandler"
            v-text="
                $t('actions.' + (subscribed ? 'unsubscribe' : 'subscribe')) + ' - ' + numberFormat(item.subscribers)
            "
        />
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { fetchSubscriptionStatus, toggleSubscriptionState } from "@/composables/useSubscriptions.js";
import { numberFormat } from "@/composables/useFormatting.js";

const props = defineProps({
    item: {
        type: Object,
        required: true,
    },
});

const subscribed = ref(null);

const channelId = computed(() => props.item.url.substr(-24));

async function updateSubscribedStatus() {
    subscribed.value = await fetchSubscriptionStatus(channelId.value);
}

function subscribeHandler() {
    toggleSubscriptionState(channelId.value, subscribed.value).then(success => {
        if (success) subscribed.value = !subscribed.value;
    });
}

onMounted(() => {
    updateSubscribedStatus();
});
</script>
