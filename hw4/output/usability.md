# Usability Improvements: Campus Customs

## 1. Saved cart for guests and logged-in shoppers

**Why we added it.** Shoppers often browse now and buy later. Baymard Institute puts average cart abandonment at about 70%, and "just browsing / not ready to buy" is the top reason shoppers give. Keeping the bag, in the browser for guests and on the account for logged-in customers, means that "later" can still turn into a sale.

**How it helps.** A returning shopper picks up where they left off instead of hunting for the same hoodie again. For the business, every saved bag is an abandoned visit that can still become an order, at no extra cost. ([Baymard, cart abandonment statistics](https://baymard.com/lists/cart-abandonment-rate))

## 2. "Items similar to this one" on product pages

**Why we added it.** A shopper who lands on a sold-out size, or a design that's not quite right, otherwise has to go back to the catalogue and start over. A row of similar items (same type, shared colors and tags, similar price, in stock first) keeps them moving toward something they'll buy.

**How it helps.** Shoppers find alternatives in one click, which matters for a store with lots of near-identical college and sport variants. For the business, recommendations are a proven revenue driver: McKinsey estimates they drive about 35% of what consumers buy on Amazon. ([UF Warrington on product recommendations](https://warrington.ufl.edu/news/how-valuable-are-online-product-recommendations/))

## 3. Focused, budget-capped shopping assistant

**Why we added it.** Every chat message is a paid AI call. Off-topic requests (homework, coding, trivia) and runaway agent loops cost money without helping anyone shop. The assistant now has detailed scope rules and per-message limits on model calls, tool calls, tokens, and time. If it can't answer within 3 attempts, it asks the shopper to rephrase instead of looping.

**How it helps.** Shoppers get short, on-topic answers quickly instead of a spinning "Thinking…". The business gets predictable AI costs and protection against what OWASP calls "unbounded consumption", where a model is pushed into excessive, costly work. ([OWASP LLM10:2025 Unbounded Consumption](https://www.stackhawk.com/blog/owasp-llm10-unbounded-consumption/))

## 4. Server-side rate limiting

**Why we added it.** Without limits, a script could guess passwords, scrape the catalogue, or send thousands of chat messages. Each of those threatens customer accounts or runs up the AI bill. Limits are enforced on the server before any expensive work. Shoppers who hit one get a friendly "try again in N seconds" message, and nothing retries in a loop.

**How it helps.** Customer accounts are protected from brute-force logins, because failures are counted per account and per IP. Normal shoppers never notice the limits, since they sit well above everyday use. For the business, it caps worst-case AI spend and keeps the site responsive for real customers. ([Akamai, defending login APIs against brute force](https://www.akamai.com/blog/developers/defending-against-a-login-api-brute-force-attack))

## 5. Duplicate-order protection

**Why we added it.** Double-clicking "Place order", or retrying after a slow page, can create two identical orders. If an identical order arrives within 5 minutes, checkout now pauses and asks the shopper to confirm they really meant to buy the same items again.

**How it helps.** Shoppers aren't charged twice by accident, so there's nothing to untangle later. For the business, it avoids the refunds, support tickets, and chargebacks that duplicate orders cause, which industry write-ups estimate at roughly 0.5–2% of transactions without safeguards. ([Seahawk, WooCommerce duplicate orders](https://seahawkmedia.com/woocommerce/woocommerce-duplicate-orders-fixes/); [Kolonell, preventing duplicate charges](https://www.kolonell.com/en/blog/prevent-duplicate-mobile-money-charges-2026))
