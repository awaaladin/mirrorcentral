/**
 * The shade catalogue as it ships in the app's Studio tabs. Names, hex values and finishes are copied
 * from scripts/seed_shades.py (served by GET /shades) and, for eye colour, from the Android app's
 * bundled catalogue (EditorShadeData.kt) - eye colour has no server-side category yet.
 *
 * Eyeliner and gele shades exist in the data but are hidden from the app's tabs for now, so they are
 * left out here on purpose: this page should only promise what the app currently shows.
 */

export type Finish = "matte" | "satin" | "glossy" | "shimmer";
export type Shade = { name: string; hex: string; finish: Finish };

/** Where a category is painted on the demo portrait, as % of the image box. */
export type Blob = { x: number; y: number; w: number; h: number; rotate?: number };

export type ShadeCategory = {
  id: string;
  label: string;
  /** What the app anchors this layer to, in plain words. */
  anchor: string;
  blend: "normal" | "multiply" | "soft-light" | "color";
  strength: number;
  blobs: Blob[];
  shades: Shade[];
};

export const shadeCategories: ShadeCategory[] = [
  {
    id: "lips",
    label: "Lips",
    anchor: "the lip contour",
    blend: "multiply",
    strength: 0.6,
    blobs: [{ x: 29.5, y: 44.6, w: 15.5, h: 5.6, rotate: -8 }],
    shades: [
      { name: "Warm Mahogany", hex: "#7B3B2E", finish: "matte" },
      { name: "Toffee Nude", hex: "#A4623B", finish: "satin" },
      { name: "Rosewood", hex: "#65323A", finish: "matte" },
      { name: "Clay Taupe", hex: "#8B5E52", finish: "satin" },
      { name: "Brick Red", hex: "#B33921", finish: "matte" },
      { name: "Oxblood", hex: "#4A1420", finish: "matte" },
      { name: "Cherry Red", hex: "#9E1B32", finish: "glossy" },
      { name: "Wine", hex: "#722F37", finish: "matte" },
      { name: "Deep Plum Berry", hex: "#6E2142", finish: "satin" },
      { name: "Burgundy", hex: "#5C0923", finish: "matte" },
      { name: "Coral Gloss", hex: "#E2725B", finish: "glossy" },
      { name: "Nude Gloss", hex: "#C98374", finish: "glossy" },
    ],
  },
  {
    id: "foundation",
    label: "Foundation",
    anchor: "the face oval",
    blend: "soft-light",
    strength: 0.55,
    blobs: [{ x: 44, y: 38, w: 58, h: 44 }],
    shades: [
      { name: "Porcelain Fair", hex: "#F1D5C0", finish: "satin" },
      { name: "Warm Beige", hex: "#E0AC81", finish: "satin" },
      { name: "Honey Tan", hex: "#C68863", finish: "satin" },
      { name: "Caramel", hex: "#A96A43", finish: "satin" },
      { name: "Golden Toffee", hex: "#8B5A34", finish: "matte" },
      { name: "Deep Cinnamon", hex: "#6F4228", finish: "matte" },
      { name: "Rich Cocoa", hex: "#5A3A24", finish: "satin" },
      { name: "Dark Chocolate", hex: "#3E2415", finish: "matte" },
      { name: "Deep Mystery Ebony", hex: "#2C160C", finish: "satin" },
    ],
  },
  {
    id: "eyeshadow",
    label: "Eyeshadow",
    anchor: "the eyelid, lifted toward the brow",
    blend: "multiply",
    strength: 0.5,
    blobs: [
      { x: 21, y: 29, w: 15, h: 5.2, rotate: -6 },
      { x: 45, y: 25.4, w: 17, h: 5, rotate: -14 },
    ],
    shades: [
      { name: "Golden Bronze", hex: "#B8752E", finish: "shimmer" },
      { name: "Copper Shimmer", hex: "#B36A34", finish: "shimmer" },
      { name: "Tangerine Pop", hex: "#D9702E", finish: "satin" },
      { name: "Deep Plum Brown", hex: "#5A3A44", finish: "matte" },
      { name: "Charcoal Smoke", hex: "#3A3532", finish: "matte" },
      { name: "Jet Black Matte", hex: "#1B1714", finish: "matte" },
      { name: "Champagne Gold", hex: "#D4AF6A", finish: "shimmer" },
      { name: "Espresso Brown", hex: "#4A3123", finish: "matte" },
    ],
  },
  {
    id: "eye-colour",
    label: "Eye colour",
    anchor: "the iris landmarks",
    blend: "color",
    strength: 0.9,
    blobs: [
      { x: 20.8, y: 30.9, w: 4.2, h: 2.8 },
      { x: 44.2, y: 26.1, w: 4.6, h: 3 },
    ],
    shades: [
      { name: "Warm Brown", hex: "#4E2E1B", finish: "satin" },
      { name: "Hazel", hex: "#6B4423", finish: "satin" },
      { name: "Honey Amber", hex: "#9A6324", finish: "shimmer" },
      { name: "Forest Green", hex: "#3A5F3A", finish: "satin" },
      { name: "Ocean Blue", hex: "#2E5C7A", finish: "satin" },
      { name: "Storm Gray", hex: "#5B6066", finish: "satin" },
      { name: "Violet", hex: "#5B3A6E", finish: "shimmer" },
    ],
  },
  {
    id: "blush",
    label: "Blush",
    anchor: "the cheek, angled toward the temple",
    blend: "multiply",
    strength: 0.45,
    blobs: [{ x: 51, y: 32, w: 24, h: 12, rotate: -20 }],
    shades: [
      { name: "Rich Terracotta", hex: "#C1552E", finish: "satin" },
      { name: "Warm Brick", hex: "#B33921", finish: "matte" },
      { name: "Deep Berry", hex: "#8E2A4E", finish: "satin" },
      { name: "Burnt Sienna", hex: "#A85327", finish: "matte" },
      { name: "Vibrant Fuchsia", hex: "#C2226E", finish: "shimmer" },
      { name: "Deep Coral", hex: "#E2603E", finish: "satin" },
    ],
  },
  {
    id: "brows",
    label: "Brows",
    anchor: "the brow rows, filled between upper and lower edge",
    blend: "multiply",
    strength: 0.7,
    blobs: [
      { x: 23, y: 21.6, w: 15, h: 3.2, rotate: -8 },
      { x: 45.5, y: 18.4, w: 18, h: 3.4, rotate: -14 },
    ],
    shades: [
      { name: "Jet Black", hex: "#1C1611", finish: "matte" },
      { name: "Espresso Brown", hex: "#3B2418", finish: "matte" },
      { name: "Warm Chocolate", hex: "#4E2F1D", finish: "matte" },
      { name: "Soft Auburn", hex: "#6B3A22", finish: "satin" },
      { name: "Ash Taupe", hex: "#5C4A3E", finish: "matte" },
    ],
  },
];

export const lashStyles = [
  { name: "Natural", note: "Short, sparse and soft." },
  { name: "Wispy", note: "Longer strokes, still light." },
  { name: "Dramatic", note: "Dense, long and dark." },
  { name: "Doll eye", note: "Full and the darkest of the four." },
] as const;

/** Total colour shades across the tabs shown above (lash styles are counted separately). */
export const shadeCount = shadeCategories.reduce((sum, category) => sum + category.shades.length, 0);
