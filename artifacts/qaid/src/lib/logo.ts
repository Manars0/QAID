/**
 * QAID logo configuration.
 * Single source of truth — import `useLogoSrc` wherever the logo is rendered.
 *
 * light: dark text + teal icon  → works on white / light-grey backgrounds
 * dark:  white text + teal icon → works on dark backgrounds
 */
export const LOGOS = {
  light: "/qaid-logo.png",
  dark:  "/qaid-logo-dark.png",
} as const;

/** Return the correct logo path for the active theme. */
export function getLogoSrc(theme: "light" | "dark" | string): string {
  return theme === "dark" ? LOGOS.dark : LOGOS.light;
}
