<template>
    <ModalComponent @close="$emit('close')">
        <h2 v-t="'actions.create_group'" />
        <div class="flex flex-col">
            <input v-model="groupName" class="my-4 input" type="text" :placeholder="$t('actions.group_name')" />
            <button v-t="'actions.create_group'" class="ml-auto btn w-max" @click="createGroup()" />
        </div>
    </ModalComponent>
</template>

<script setup>
import ModalComponent from "./ModalComponent.vue";
import { ref } from "vue";

const props = defineProps({
    onCreateGroup: {
        required: true,
        type: Function,
    },
});

const emit = defineEmits(["close"]);

const groupName = ref("");

function createGroup() {
    props.onCreateGroup(groupName.value);
    emit("close");
}
</script>
