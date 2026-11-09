const slides = [...document.querySelectorAll(".slide")]
const parameters = new URLSearchParams(location.search)
const printing = parameters.has("print")
let active = Math.max(0, Math.min(slides.length - 1, (Number.parseInt(location.hash.slice(1), 10) || 1) - 1))
function fit() {
  const scale = Math.min(innerWidth / 1600, innerHeight / 900)
  document.querySelector(".deck").style.transform = `scale(${scale})`
}
function show(index) {
  active = Math.max(0, Math.min(slides.length - 1, index))
  slides.forEach((slide, position) => {
    slide.hidden = !printing && position !== active
    slide.classList.toggle("play", position === active && !parameters.has("static") && !printing)
  })
  if (!printing) history.replaceState(null, "", `#${active + 1}`)
}
addEventListener("keydown", (event) => {
  if (["ArrowRight", "PageDown", " "].includes(event.key)) { event.preventDefault(); show(active + 1) }
  if (["ArrowLeft", "PageUp"].includes(event.key)) { event.preventDefault(); show(active - 1) }
  if (event.key === "Home") show(0)
  if (event.key === "End") show(slides.length - 1)
  if (event.key.toLowerCase() === "r") {
    slides[active].classList.remove("play")
    requestAnimationFrame(() => requestAnimationFrame(() => slides[active].classList.add("play")))
  }
})
addEventListener("hashchange", () => show((Number.parseInt(location.hash.slice(1), 10) || 1) - 1))
addEventListener("resize", fit)
show(active)
if (!printing) fit()
