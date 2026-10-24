<script setup>
const homeUrl = import.meta.env.BASE_URL;
</script>

<template>
    <div class="flex min-h-[88vh] flex-col items-center justify-center">
        <h1 class="text-9xl! font-bold">404</h1>
        <h2 v-t="'info.page_not_found'" class="text-2xl!" />
        <a v-t="'actions.back_to_home'" class="mt-16 btn" :href="homeUrl" />
    </div>
</template>
