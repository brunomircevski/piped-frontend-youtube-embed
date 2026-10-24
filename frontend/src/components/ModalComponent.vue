<template>
    <DialogRoot :open="true" @update:open="onOpenChange">
        <DialogPortal>
            <DialogOverlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm transition-opacity" />
            <DialogContent
                class="fixed top-1/2 left-1/2 z-50 max-h-[90vh] w-max max-w-[92vw] min-w-[min(92vw,22rem)] -translate-1/2 overflow-y-auto rounded-2xl border border-(--border) bg-(--surface-raised) p-6 text-(--text) shadow-(--shadow) focus:outline-none"
            >
                <DialogClose as-child>
                    <button
                        type="button"
                        class="absolute top-3 right-3 flex size-8 items-center justify-center rounded-full text-muted hover:bg-(--surface-muted) hover:text-(--text)"
                    >
                        <i-fa6-solid-xmark />
                    </button>
                </DialogClose>
                <slot></slot>
            </DialogContent>
        </DialogPortal>
    </DialogRoot>
</template>

<script setup>
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogRoot } from "reka-ui";

const emit = defineEmits(["close"]);

function onOpenChange(open) {
    if (!open) {
        emit("close");
    }
}
</script>
