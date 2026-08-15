const eye = document.getElementById("eye");
const pupilGroup = document.getElementById("pupilGroup");
const eyeWrap = document.getElementById("eyeWrap");

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (!reduceMotion) {
  window.addEventListener("pointermove", (event) => {
    const rect = eyeWrap.getBoundingClientRect();
    const x = ((event.clientX - (rect.left + rect.width / 2)) / (rect.width / 2));
    const y = ((event.clientY - (rect.top + rect.height / 2)) / (rect.height / 2));
    const px = Math.max(-1, Math.min(1, x)) * 13;
    const py = Math.max(-1, Math.min(1, y)) * 8;
    pupilGroup.style.transform = `translate(${px}px, ${py}px)`;
  });

  const blink = () => {
    if (!document.hidden) {
      eye.classList.add("blink");
      setTimeout(() => eye.classList.remove("blink"), 430);
    }
    const next = 6500 + Math.random() * 9000;
    setTimeout(blink, next);
  };
  setTimeout(blink, 5000);

  eyeWrap.addEventListener("mouseenter", () => {
    eyeWrap.style.filter = "brightness(1.08)";
  });
  eyeWrap.addEventListener("mouseleave", () => {
    eyeWrap.style.filter = "";
  });
}

const revealTargets = document.querySelectorAll(
  ".section, .terminal-section, .open-source-card, .final-cta"
);

revealTargets.forEach((element) => element.classList.add("reveal"));

if ("IntersectionObserver" in window && !reduceMotion) {
  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  revealTargets.forEach((element) => observer.observe(element));
} else {
  revealTargets.forEach((element) => element.classList.add("visible"));
}
