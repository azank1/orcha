/**
 * Metis owl paths — round head, soft crown, upright perched body.
 * Locked SVG geometry (viewBox 0 0 100 100).
 */
export const OWL_VIEWBOX_SIZE = 100

/** Single smooth silhouette — round head flowing into torso. */
export const BODY_PATH =
  'M61,15 Q50,11.5 39,15 C31,16 25,23 25,32 V77 c0,9 7,15 15,15 h20 c8,0 15,-6 15,-15 V32 C75,23 69,16 61,15 Z'

export const BEAK_PATH = 'M50,41.8 L54.2,46.5 L50,51.2 L45.8,46.5 Z'

export const FOOT_LEFT = { x: 41, y: 91, width: 6, height: 7, rx: 3 }
export const FOOT_RIGHT = { x: 53, y: 91, width: 6, height: 7, rx: 3 }

export const PERCH_RECT = { x: 10, y: 96, width: 80, height: 3, rx: 1.5 }

export const EYE_LEFT_CENTER = { x: 36, y: 30 }
export const EYE_RIGHT_CENTER = { x: 64, y: 30 }
export const EYE_DIAMETER = 18
