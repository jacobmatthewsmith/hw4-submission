import type { Product } from './api'

// garment_type values in the database are inconsistent ("hoodie", "pullover hoodie",
// "short-sleeve T-shirt", ...), so categories match on loose keywords.
export const categories = [
  { key: 'hoodie', label: 'Hoodies', match: ['hood'] },
  { key: 'crewneck', label: 'Crewnecks', match: ['crewneck', 'crew-neck sweat', 'mockneck', 'raglan'] },
  { key: 'quarter-zip', label: 'Quarter-Zips', match: ['quarter-zip'] },
  { key: 't-shirt', label: 'T-Shirts', match: ['t-shirt', 'performance shirt'] },
  { key: 'jacket', label: 'Jackets', match: ['jacket'] },
] as const

export type CategoryKey = (typeof categories)[number]['key']

export function categoryOf(product: Product): CategoryKey | undefined {
  const type = product.garment_type.toLowerCase()
  // Hoodies are checked first so "full-zip hooded sweatshirt" isn't filed as a jacket.
  return categories.find((c) => c.match.some((m) => type.includes(m)))?.key
}
