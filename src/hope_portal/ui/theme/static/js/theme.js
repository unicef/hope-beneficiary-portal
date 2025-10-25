document.addEventListener("DOMContentLoaded", function () {
    const FONT_KEY = 'user_font_size';

    const toggler = document.getElementById("theme-toggler");
    const HTML = document.getElementsByTagName('html')[0];
    const stored_theme = localStorage.getItem("theme") || "dark"
    const stored_size = localStorage.getItem(FONT_KEY) || 'font-size-normal'; // Default
    const body = document.body;
    const selectors = body.querySelectorAll('.font-size-selector div');
    const FONT_CLASSES = ['font-size-normal', 'font-size-medium', 'font-size-big'];

    HTML.dataset.theme = stored_theme;
    toggler.checked = (HTML.dataset.theme === "dark");
    HTML.dataset.theme = localStorage.theme || "dark";
    localStorage.setItem("theme", HTML.dataset.theme);
    toggler.addEventListener("click", () => {
        HTML.dataset.theme = toggler.checked ? "dark" : "light"
        localStorage.theme = HTML.dataset.theme;
    })

    function applyFontSize(newSize) {
        HTML.classList.remove(...FONT_CLASSES);
        HTML.classList.add(newSize);
        localStorage.setItem(FONT_KEY, newSize);
        let old_selection = body.querySelector('.font-size-selector div.selected');
        if (old_selection){
            old_selection.classList.remove("selected");
        }
        let selection = body.querySelector(`.font-size-selector div[data-size=${newSize}]`);
        if (selection){
            selection.classList.add("selected");
        }
    }

    if (selectors) {
        for (const selector of selectors) {
            selector.addEventListener('click', (event) => {
                applyFontSize(event.target.dataset.size);
            });
        }
    }
   applyFontSize(stored_size);
})
