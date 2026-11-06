deckScene("mechanic", {
  init(el) {
    const paths = [...el.querySelectorAll(".mech-map path")]
    el.querySelectorAll(".runner").forEach((runner, i) => deckKit.followPath(runner, paths[i]))
  },
})
