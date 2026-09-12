# FORGEDIS Identity System v1.0

Status: LOCKED for public storefronts.

## Brand architecture
- FORGEDIS = master brand.
- FORGEDIS Consulting = primary commercial activity.
- ARIA = proprietary technology family.
- ARIA Facility = autonomy and accessibility.
- ARIA Kids = education and learning.
- ARIA Industrial = business operations.
- NEXORA = internal system, not presented as a public product in this redesign.

## Core idea
**De l'intelligence à l'action.**

FORGEDIS translates analysis into action. The visual language is built around a restrained Action Path: line, decision point, progression, action.

## Visual foundations
- Direction: Precision × Engineering.
- Light theme: warm ivory, graphite, ink, vermilion action accent.
- Dark theme: deep ink, warm off-white, graphite neutrals, same vermilion action accent.
- Vermilion is functional: CTA, active state, action point. It is not decorative.
- Typography: editorial serif for major messages, clean sans for interface and body copy.
- Layout: precise grid, controlled asymmetry, large breathing spaces, few rounded cards, almost no decorative shadows.

## Themes
Both light and dark themes are first-class experiences. The visitor's OS preference is respected initially, then the explicit visitor choice is saved locally.

## Public page hierarchy
1. FORGEDIS homepage: brand promise → Consulting → method → ARIA technology → Facility/Kids/Industrial → contact.
2. Consulting: diagnostic → audit/strategy → automation → training/deployment → contact.
3. Facility: human, calm, autonomy-oriented.
4. Kids: curious and educational without becoming childish.
5. Industrial: technical, operational, structured, without cyberpunk aesthetics.

## Anti-template rules
Forbidden as default art direction:
- blue/purple AI gradients;
- generic neural-network visuals;
- humanoid robots, glowing brains, holograms;
- decorative pills and cards everywhere;
- fabricated dashboards or fabricated proof;
- decorative use of the action color.

## Content integrity
Never invent or publish client logos, testimonials, partner logos, certifications, revenue, satisfaction percentages, project counts, performance gains or other proof. Concept mockups are visual references only.

## Functional preservation
The redesign concerns public storefronts. Existing product applications, subscription flows, authentication and backend code must not be redesigned or removed as part of this phase. Public showcase pages link onward to the existing product routes.

## Accessibility and responsive
- Respect reduced-motion preferences.
- Maintain keyboard-focus visibility.
- Maintain WCAG AA contrast for text and controls.
- Mobile is a deliberate layout, not a compressed desktop version.

## Source of truth
`forgedis.css` contains shared visual tokens and layout rules. `forgedis.js` contains theme behavior. Public pages must use these shared foundations unless a documented product-specific exception is required.
