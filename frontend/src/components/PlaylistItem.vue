<template>
    <div class="flex flex-col justify-between">
        <router-link :to="props.item.url" class="inline-block">
            <div class="relative">
                <img
                    loading="lazy"
                    class="aspect-video w-full rounded-xl bg-(--surface-muted) object-cover"
                    :src="props.item.thumbnail"
                />
            </div>
            <p
                class="line-clamp-2 pt-3 text-[0.9375rem] leading-snug font-semibold"
                :title="props.item.name"
                v-text="props.item.name"
            />
        </router-link>
        <p v-if="props.item.description" class="mt-1 line-clamp-2 text-sm text-muted" v-text="props.item.description" />

        <router-link
            v-if="props.item.uploaderUrl"
            class="mt-1 line-clamp-1 block text-sm text-muted hover:text-(--text)"
            :to="props.item.uploaderUrl"
        >
            <p class="leading-tight">
                <span v-text="props.item.uploaderName" />
                <i-fa6-solid-check v-if="props.item.uploaderVerified" class="ml-1.5" />
            </p>
        </router-link>
        <a
            v-else-if="props.item.uploaderName"
            class="mt-1 line-clamp-1 block text-sm text-muted hover:text-(--text)"
            v-text="props.item.uploaderName"
        />

        <template v-if="props.item.videos >= 0">
            <span class="mt-1 text-sm font-medium text-muted" v-text="`${props.item.videos} ${$t('video.videos')}`" />
        </template>
    </div>
</template>

<script setup>
const props = defineProps({
    item: {
        type: Object,
        required: true,
    },
});
</script>
