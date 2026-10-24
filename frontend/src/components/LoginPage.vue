<template>
    <div class="mt-8 flex items-center justify-center gap-2">
        <h1 v-t="'titles.login'" class="text-2xl font-bold" />
        <i-fa6-solid-circle-info class="cursor-help text-muted" :title="$t('info.login_note')" />
    </div>
    <div class="flex w-full justify-center px-3">
        <form class="mt-6 grid w-full max-w-sm gap-3 card p-6">
            <div>
                <input
                    v-model="username"
                    class="input w-full"
                    type="text"
                    autocomplete="username"
                    :placeholder="$t('login.username')"
                    :aria-label="$t('login.username')"
                    @keyup.enter="login"
                />
            </div>
            <div>
                <input
                    v-model="password"
                    class="input w-full"
                    type="password"
                    autocomplete="password"
                    :placeholder="$t('login.password')"
                    :aria-label="$t('login.password')"
                    @keyup.enter="login"
                />
            </div>
            <div>
                <Button v-t="'titles.login'" custom-class="btn-primary w-full" @click="login" />
            </div>
        </form>
    </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { fetchJson, authApiUrl, getAuthToken, hashCode } from "@/composables/useApi.js";
import { setPreference } from "@/composables/usePreferences.js";
import Button from "./ui/Button.vue";

const router = useRouter();
const { t } = useI18n();

const username = ref(null);
const password = ref(null);

onMounted(() => {
    //TODO: Add Server Side check
    if (getAuthToken()) {
        router.push(import.meta.env.BASE_URL);
    }
});

onActivated(() => {
    document.title = t("titles.login") + " - Piped";
});

function login() {
    if (!username.value || !password.value) return;
    fetchJson(authApiUrl() + "/login", null, {
        method: "POST",
        body: JSON.stringify({
            username: username.value,
            password: password.value,
        }),
    }).then(resp => {
        if (resp.token) {
            setPreference("authToken" + hashCode(authApiUrl()), resp.token);
            window.location = import.meta.env.BASE_URL; // done to bypass cache
        } else alert(resp.error);
    });
}
</script>
