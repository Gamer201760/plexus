deckScene("flowchart", {
  init(el) {
    deckKit.followPath(el.querySelector(".runner"), el.querySelector("#fc-main"))
  },
})
