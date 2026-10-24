// Some mobile browsers (Brave's bottom toolbar) draw over the bottom of the page
// without shrinking the area fixed elements are laid out in, so `bottom: 0`
// ends up underneath them. The visual viewport does shrink, so the gap between
// a probe fixed at `bottom: 0` and the visual viewport's bottom edge is the part
// that is covered. It is exposed as --toolbar-inset (see --bottom-inset in app.css).
export function trackBottomInset() {
    const viewport = window.visualViewport;
    if (!viewport) return;

    const probe = document.createElement("div");
    probe.style.cssText = "position:fixed;bottom:0;left:0;width:0;height:0;pointer-events:none;visibility:hidden";
    document.body.appendChild(probe);

    let frame = 0;
    function update() {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            const covered = probe.getBoundingClientRect().top - (viewport.offsetTop + viewport.height);
            // Pinch-zoom and the on-screen keyboard also shrink the visual viewport;
            // following those would float the bars over the page.
            const typing = document.activeElement?.matches("input, textarea, select, [contenteditable='true']");
            const inset = viewport.scale > 1.01 || typing ? 0 : Math.max(0, Math.round(covered));
            document.documentElement.style.setProperty("--toolbar-inset", `${inset}px`);
        });
    }

    viewport.addEventListener("resize", update);
    viewport.addEventListener("scroll", update);
    window.addEventListener("scroll", update, { passive: true });
    document.addEventListener("focusin", update);
    document.addEventListener("focusout", update);
    update();
}
