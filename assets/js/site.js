(() => {
  "use strict";

  const isTeleVault = window.location.pathname.startsWith("/tele-vault");
  document.body.classList.add(isTeleVault ? "televault-theme" : "shagiz-theme");

  if (!document.querySelector('link[data-brand-styles]')) {
    const brandStyles = document.createElement("link");
    brandStyles.rel = "stylesheet";
    brandStyles.href = "/assets/css/brand-overrides.css";
    brandStyles.dataset.brandStyles = "true";
    document.head.appendChild(brandStyles);
  }

  if (!document.querySelector('link[rel="icon"]')) {
    const icon = document.createElement("link");
    icon.rel = "icon";
    icon.type = "image/svg+xml";
    icon.href = isTeleVault
      ? "/assets/brand/televault-mark.svg"
      : "/assets/brand/shagiz-mark.svg";
    document.head.appendChild(icon);
  }

  if (!document.querySelector('meta[name="theme-color"]')) {
    const themeColor = document.createElement("meta");
    themeColor.name = "theme-color";
    themeColor.content = isTeleVault ? "#0A84FF" : "#07152F";
    document.head.appendChild(themeColor);
  }

  const toggle = document.querySelector("[data-nav-toggle]");
  const navigation = document.querySelector("[data-navigation]");

  if (toggle && navigation) {
    const closeNavigation = () => {
      navigation.dataset.open = "false";
      toggle.setAttribute("aria-expanded", "false");
    };

    toggle.addEventListener("click", () => {
      const isOpen = navigation.dataset.open === "true";
      navigation.dataset.open = String(!isOpen);
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });

    navigation.addEventListener("click", (event) => {
      if (event.target instanceof HTMLAnchorElement) {
        closeNavigation();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeNavigation();
        toggle.focus();
      }
    });
  }

  const year = document.querySelector("[data-current-year]");
  if (year) {
    year.textContent = String(new Date().getFullYear());
  }
})();
