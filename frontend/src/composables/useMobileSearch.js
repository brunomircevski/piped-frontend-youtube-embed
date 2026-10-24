import { ref } from "vue";

// NavBar owns the mobile search field; the bottom nav asks it to open through this.
export const mobileSearchRequest = ref(0);

export function openMobileSearch() {
    mobileSearchRequest.value++;
}
