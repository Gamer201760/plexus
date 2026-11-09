export type TransportMode =
  | "bus"
  | "air"
  | "river"
  | "winter_road"
  | "ferry"
  | "ice_crossing"
  | "pontoon_bridge"

export interface Glyph {
  readonly strokes: readonly string[]
  readonly dots: readonly (readonly [number, number, number])[]
}

export const TRANSPORT_GLYPHS: Record<TransportMode, Glyph> = {
  bus: {
    strokes: ["M5 18V6a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v12Z", "M5 11h14", "M8 18v3", "M16 18v3"],
    dots: [
      [8, 15, 1],
      [16, 15, 1],
    ],
  },
  air: {
    strokes: [
      "M12 2.75c.83 0 1.4.95 1.4 2.1v4.4l7.1 4.15v1.85l-7.1-2.05v4.3l2.1 1.6v1.4L12 19.6l-3.5.9v-1.4l2.1-1.6v-4.3L3.5 15.25V13.4l7.1-4.15v-4.4c0-1.15.57-2.1 1.4-2.1Z",
    ],
    dots: [],
  },
  river: {
    strokes: [
      "M3.5 14.5h17l-2.3 4H5.8Z",
      "M7.5 14.5V10h7l2.5 4.5",
      "M10.5 10V6.5",
      "M2.5 21.5c1.6 0 1.6-.9 3.2-.9s1.6.9 3.2.9 1.6-.9 3.2-.9 1.6.9 3.2.9 1.6-.9 3.2-.9 1.6.9 3.1.9",
    ],
    dots: [],
  },
  winter_road: {
    strokes: [
      "M5 21.5 9.5 10",
      "M19 21.5 14.5 10",
      "M12 13.5v1.5",
      "M12 18v2.5",
      "M12 2.5v5.5",
      "M9.6 3.9l4.8 2.7",
      "M14.4 3.9l-4.8 2.7",
    ],
    dots: [],
  },
  ferry: {
    strokes: ["M2.5 6.5h6", "M15.5 17.5h6", "M8.5 6.5 15.5 17.5"],
    dots: [
      [8.5, 6.5, 1.8],
      [15.5, 17.5, 1.8],
    ],
  },
  ice_crossing: {
    strokes: [
      "M12 2.5v19",
      "m3.8 7.25 16.4 9.5",
      "m3.8 16.75 16.4-9.5",
      "M9.5 4 12 5.6 14.5 4",
      "M9.5 20 12 18.4 14.5 20",
    ],
    dots: [],
  },
  pontoon_bridge: {
    strokes: [
      "M2.5 15.5h19",
      "M4 15.5c2-4 5-6 8-6s6 2 8 6",
      "M8 11.4v4.1",
      "M12 9.5v6",
      "M16 11.4v4.1",
      "M4 19.5h16",
    ],
    dots: [],
  },
}
