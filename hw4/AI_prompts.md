# AI Prompts Log — Campus Customs (HW 4)

All prompts I sent to the AI coding assistant, organized by problem. Prompts are copied verbatim. Follow-up prompts include a bracketed note explaining why they were needed.

---

## Problem 1: Project Setup

**Prompt:**

> Ok we are going to work in folder 4 of the ai foundations document

**Follow-up:**

> Sorry - yes HW 4 folder

[Needed because "folder 4" matched both the `HW 4` and `Lecture 4` folders, so the assistant asked which one I meant.]

**Follow-up:**

> Ok I'm going to start with some table setting. We are going to build a website for a fictional brand called campus customs - it also needs a helpful chatbot. This is going to be react + vite + typescript stack front end, and a python fast API backend which should be powered by a pydantic agent. Shoppers should be able to browse products create an account, chat about merch, and see matching items that get queriued appear on the page - and honest answers about price and stock from a datatbase.
>
> We have a campus.customs.db file (in the zipped file) in the folder (i jutst added this)> This has tables for product catalogue, inventory by size, and fictional users forus to test logging in with and from. The file of users also has hashed passwords. Product image file paths are in the catalogue table. You need to reasearch this website (yalebulldogblue.com to learn the style of campus customs page and information for your agent prompt.
>
> We need to uyse the portkey_APi_Key. We're going to use open ai chat gpt model 5.6 for this assignment. We're going to work one problemn at a time. an important feature of this homework is that I am given promtps by my instructor, and i'll be writing to you in my own words. At the end of this project we're going to push this project to a public github repo and submti the repo URL on canvas (DO NOT commit the database or product images in this final submission). If you could go ahead and include the instructions in this paragraph, polished up, into the harness file that we build, tnat would be great.
>
> Ok so start by unzipping the file. We shoulkd have data/campus_customs.db (which is an sqlite database with the tables Catalogue, inventory, users (there should be one test user already there).
> data/products/ - which should have product images, paths match the catalogue table

[Needed to give the project brief, unzip the provided data, and have the instructions saved into a harness file.]

**Follow-up:**

> gpt-5.6-sol

[Needed because the assistant asked for the exact model ID Portkey expects for GPT-5.6.]

**Follow-up:**

> ok and can you rename the harness file harness.md

[Needed to give the harness file the name I wanted for the submission.]

---

## Problem 2: AI Prompts Log

**Prompt:**

> Ok PROBLEM 1 - we need to create an AI_prompts.md folder where we will log all of my prompts. This is for grading purposes of this assignment. this is where you will log all the prompts i sent you, organized by problem. Each prompt should be labeled under a problem & title category (i.e. one section for each problem)
>
> * The problem number and title
> * at leats on prompt i typed under that category
> * Any follow up prompts if I needed them, and one sentence description that you will insert in brackets of why this prompt was needed.
>
> A functional website is the only other deliverable.

**Follow-up:**

> ok update - that was problem 2! can you update the log?

[Needed because I had mislabeled this step as Problem 1. It is Problem 2 in the assignment, so the setup work becomes Problem 1.]

---

## Problem 3: Build the Campus Customs Website

**Prompt:**

> ok problem 3 - build a campus customs website. We need to scaffold a react + vite _ typescript front end for campus customs. there should be a nav bar at the top that links to the main pages:
>
> The links for the top:
>
> Home
>
> products
>
> About us
>
> Log in
>
> Create an account
>
> Can you pull campus customs style wording from the yalebulldogblue.com website? I.e. match tone and style from this website. for the home and about us pages expecially> DO NOT Copy the website directly - this should be written in your own voice. Please feel free to make it slightly more humorous than the original - and again it should be novel
>
> On the products page, show the product iumages from the catalogue (use the image pahts you find in the database) with basic proiduct info (name, price, short description)
>
> Each product should open its own single item page (similar to other retail websites) There should be a alrge image on the left side, with full product detaisl and text on thsi other - includeing description, price, sizes/stock clickign a tile on products page sghould take sghopper tot htis page.
>
> In the bottom right, there shoudl eb a chatbot dfeatyure. a floating chat panel is fine. it does nto need to talk or interface with an agent yet. - we'll build this backend later. Accoridng to professor - "a stub" that will call this backend later is enough for th eporbopem
>
> You will need a small AP soon to read the database. Yous hodul startw itht FASTAPI app in backend/main.py for this for now, to serve up the products and images. Thsi should then grow into the agent backend in problem 5

---

## Problem 4: Create an Account and Log In

**Prompt:**

> Problem 4 - creating an account log in
>
> We're going to create an account login - it will have a first name, a last name, email, and password. I thsould also have a verify password infromation field, that should validate whether the passwords match (I'm sure a tool or osmehting existss on the internet for this)
>
> so you should be able to create an account, but you should also be able to click on something to login - this should just be email and password. ANd the user shoudl eb able to use their email and password to log in. The passwords are hashed, so there will need to be somethign to hash/unshash them. and this file should be very secure (in a normal way - just want toi make sure it is not publicly published on the internet.
>
> new accounts go int ot eh users table (the one that already exists(). Make sure to store this passwords securely so that no hackers can get into them (*per the above hashing instructings0
>
> The seed database already has some users (make sure these ra epreserved asis)
>
> There should be a test user *(email: test@campuscustoms.yale.edu, pw: password)
>
> I'll need to confirm i can log in once you've build the log in feature, and I'll also need to cionfirm that the brand new account work flow also works.
>
> Can you also update output/harness.md with how the auth works and how users and passwords are stored and protects)

**Follow-up:**

> Ok test for problem 4 complete

[Needed to confirm I had tested both logging in as the test user and creating a brand-new account in the browser.]


---

## Problem 5: Build the Pydantic AI Agent Backend

**Prompt:**

> Ok problem 5 - build the pydanticAI agent backend
>
> Next we're going to build the chatbot we talekjd about earlier - this will be a pydanticAI agent behind fastAPI. this should be plugged in the front end widget you built in a previous problem as well. Put the API app in backend/main.py this is the file that we will run with uvicorn. The agent shoukld be run out of these 4 files next tot he above (you can check the hw 3 folder for an example, but I'm not certain that homework worked well so take it with a grain of salt - no need to get hung up on hw 3 structure)
>
> backend/prompts/prompt.md (this will be the system prompt and this file will grow later)
>
> backend/agent.py - for the agent entry & wiring
>
> backend/tools.py - tools the agent can call
>
> backend/models.py - Pydantic / pydanticAI structured tooles
>
> in main.py, we need to expose a chat route so that a message from the website returns a reply with the agent, and whatever else you need for products/auth. You will need to have the api key hooked up this agent
>
> Other agent instructions (this should go in prompts/prompt.md)
>
> The agent should speak in campus customs voice (similar to their website). A saftey thing we should make sure to inluce is that the chatbot should reject a question that is not about campus customs merch - i.e. do not use tokens on someone elses asks. we'll likely modify this later, but I wanted to make sure i didnt forget
>
> You should atrt por update types in models.py for chat replies and prodyct cards as needed
>
> in output/harness.md note how the front end talks to fastapi and how the agent is loaded (prompt file + model)
>
> Make sure the backend runs from the backend/ folder like this:
>
> uvicorn main:app --reload --port 8000


---

## Problem 6: Tools for Product Info and Stock

**Prompt:**

> Ok next is porblem 6: tools: product info and stock
>
> We need to give the agent tools so that it is more powerful when it's chatting with a customer - it needs tools that look up real information from campus_customs.db
>
> the tools should eb around
>
> Product description
>
> price
>
> How many are in stock - by size when the customer asks
>
> the agent must use the database and not make up informaiton when it cant find it or if anything is ambigous. If anythign is ambigous with the customer, the agent can always ask a follow up wiuestion. Info should never be frabirctaed.
>
> it should nto invent prices or quantities. If a size is out of stock, be sure to say so clearly (i.e. say that is out of stock rather than "i found it in stock" when all you could find was a record of the item have existed at one point but the inventory is zero)
>
> We need to add info to prompts/prompt.md so the agent knows to call on these tools for price and stock questions. It needs to add or update return types in mdoels.py
>
> Also add to output/harness, each tool and explina which model fields you chose for look up results and why. You could create a new table or add it to the original table - i totally defer to you on which is more efficient/streamlined/make you more efficient and less error prone.


---

## Problem 7: Chat Search That Updates the Page

**Prompt:**

> Problem 7 - chat search that updates the page.
>
> We're going to add a cool feature - you're going to pbuild something that will update the page in addition to the chat. I.e. when the chat brings up the tshirt options, for exmaple, the page will also update with those items, as if the user had searched for them. The agent should search the catalgoue, and the website shoudl show matching items as product cards. This is an API contract - the agent should return strucutred product matches and then the front end renders them on the website.
>
> After the product cards are loaded by the new feature, please double check that the same single item page feature we built still works - i.e. the images lead to the larger page for that item, and the relationship between the tiles and the expanded view of that item is still in place (large image and full info)
>
> Update prompts/prompt.md and output/harness.md so it's clear how search results reach the page


---

## Problem 8: Customer Memory

**Prompt:**

> Ok next is problem 8 - Customer memory
>
> When a customer is logged in, we want to save their chat history in a the database in an appropriate table/structure, and reload the chat when they return. The agent should know who is chatting (their name, email). Please add that to the agent deps (or an equivalent clear pattern and tools the agent can call (i.e. it should say "hi NAME" inserting the persons name)
>
> Also - can you add a feature wher eif a customer is on a page fo a specific merch item, the chat agent can read the page they are on and answer questions abotu that item (again important that they are matching the rigth item and not making anything up). Hint: it's fine to put code in the agent context>
>
> Guests shoudl still be able to chat - you should only load history for logged in users, and the histopry should always match that user.
>
> document in output/harness.md - how user chat history is stored, what customer fields the agent sees, and how page context is passed. for the fields the agent sees, this should just be name and email for now.


---

## Problem 9: Usability Improvements

**Prompt:**

> This is problem 9: Usability imporvements.
>
> Ok next we're going to add improvedments to the website and the backend usability/improvements.
>
> Front end improvement number 1 (save items in cart for when they return):
>
> For both guests AND logged in users, please save what they have in their cart for when they return to site. I.e. even a guest customer should be able to return to the site and see what is in their cart (this is one of myfavorite features on other websites). It should definitely work for logged in users
>
> Front end improvement number 2:
> Add a similar items to this bar at the bottom of the exapnded screen.
>
> For each item, when you click on the tile it brings you into the expanded view (with picture ont he elft, and details on the right). Below that, in smaller images, show "items similar to this one" where customers can see items like the one below - feel free to do some researhc on what this typically looks like on websites to build out this feature) .
>
> Backend improvement number 1: Make the chat more efficient be restricting what/how it can reply to customers.
>
> Add very detaield instructions to the harness.md and the prompts for the egant to restrict customers to taksing chats about the product. Also, kill the chat if it starts working harder than expected or gets stuck. Feel free to tell the customer to pleade ask the question a different way ratehr than have the model loop indefintiely. If it cant asnwer the question after 3 attempts to answer it, return an answer askign them to rephrase the question. I have additional context I had chat gpt cook up here:
>
> "
>
> Add server-side rate limiting to this retail website to reduce abuse and unexpected API costs.
> First, inspect the existing backend and deployment setup. Apply limits only to features that already exist; don’t create new login or checkout functionality.
> Use these configurable starting limits:
>
> * Login: 5 failed attempts per account per 15 minutes, plus a separate IP-based limit to prevent repeated attempts across accounts.
> * Search: 60 requests per minute per user or anonymous visitor.
> * Checkout: 10 submission attempts per minute per user or anonymous visitor.
> * AI assistant: 5 requests per minute and 30 per hour per user or anonymous visitor, with no more than 2 simultaneous AI requests.
>
> Enforce limits on the server before expensive work or external API calls begin. Use authenticated user IDs where available and a deployment-appropriate identifier for anonymous visitors. Don’t trust user-supplied identity or IP headers.
> Use the existing framework’s rate-limiting capabilities where suitable. If the deployment runs multiple server instances, use shared storage so the limits apply across all instances.
> When a limit is exceeded, return HTTP 429 with a Retry-After header. Have the frontend display a friendly message explaining when the shopper can try again, without automatically retrying in a loop.
> Keep API keys private, and avoid logging passwords, tokens, or full conversations.
> Verify that normal requests succeed, excessive requests are blocked, limits reset correctly, and one user’s activity doesn’t consume another user’s allowance. Summarize what changed and any deployment configuration required.
>
> "
>
> backend improvement number 2: prevent duplicate orders
>
> If a user orders an indentical shipment within 5 minutes of each other, decline the purchase and ask the customer to confirm that they intended to buy that item.
>
> Ok and then next - we need to write output/usability.md for each of these improvements, can you write up a blurb on:
>
> why we added them
>
> why it helps cmapus customes shopper or business. feel free to do some research to pull these reasons in. Please write a short paragrpah for each (2-3 sentences)
>
> Finally, implement these improvements. Make sure they show up in the app. For your awareness, the graders of this assignment will look for functioning features!!


---

## Problem 10: Style the Website

**Prompt:**

> Ok problem 10 - style the website
>
> We need to add a creative design to the website so it feels real. Can you make it like a mash up of call/autumn/ivy league/and back to to school (index heaviest on the fall theme). Can you give me 3 possible directions I can choose from? I want it to still be recognizbly Yale- and we want this to fee llike a very real website.
>
> We need to write a output/design.md - what we changed and why we changed it. Please make sure to give an overview of the stylistic changes we made (i.e. changes in color scheme for origninal to new). This should be concrete and short, but understandable how the page evolved). It should also include a reason why it will help customers stick around and buy.
>
> Do not implement the second part until we've chosen one of the options from part one, then implement this whole prompt

**Follow-up:**

> This is still problem 10 - can you suggest a few other novel creative ideas for a theme?

[Needed because I wanted more original theme options to compare before choosing a design direction.]

**Follow-up:**

> Could we do a stylking that is like Y2K internet fall, but in a way that is obviously toungue and cheek and not actually clunky feeling (i.e. slick feel but with a Y2K back to school fall theme? Can you render a sample of what this might look like before we fully implement?

[Needed because none of the suggested directions matched what I wanted, so I proposed my own Y2K-internet fall theme and asked for a rendered sample before implementing.]

**Follow-up:**

> No this looks so bad - can we do a Y2K alien theme? I'd like the colors to be black and green. Try rendering that and then lets go from there

[Needed because I didn't like the rendered Y2K fall sample, so I asked for a black-and-green Y2K alien theme instead.]

**Follow-up:**

> and I'm thinking like courier type font - sort of like space ship. think like clipart and and pixely version fo the alien or ufo meoji. It's sort of video game aligned, but feels like a website you might be on in literally 1999. But make sure the navigation and work flows and chat bot still work/appear in a clean way.

[Needed to refine the alien theme with specific typography (Courier), pixel-art clipart, and a 1999 video-game feel, while keeping navigation and the chatbot clean.]

**Follow-up:**

> ok and this is till prompt 10
>
> We need to write output/design.md for the rationale for this design. I want to talk about the Y2K styling being hip and in right now. Please write a good paragraph on why we chose this marketing and user experience.

[Needed to request the design rationale document, including why Y2K styling is on-trend right now, for the chosen direction.]

**Follow-up:**

> Ok this looks good - a couple small design tweaks - could you make the buttons people can click be a little more user friendly or larger - just like more obvious that someone can chat, look at merch, look at their cart. And maybe pivote to a more white background? with green and black text? But again - this looks great!

[Needed to approve the Y2K alien direction with two tweaks: larger, more obvious buttons for chat, shopping, and the cart, and a white background with green and black text.]


---

## Problem 11: Site Testing (App Check)

**Prompt:**

> Problem 11: Site Testing (app check) - I am going to test the site (please drop the link) and then we need to document it in output/app_check.html - this will be a static link someone can click on and see (and this is very important) screenshots of the website with captions (think of this as a website with a prospectus for a client to show them what the website looks like)
>
> The screenshots sections should be :
>
> of the chat checking the inventory level of an item (including an honest stock pice from the DB)
>
> The dyanmic search result cards appearing after a question about that item (ex: showing hoodies after a question about hoodies)
>
> One of the usability features we added (let's go with the shopping cart)
>
> These screenshots could be gifs showing the flow in real time, or just images
>
> Start building the html site with screenshots while i review the website - can you drop the link for me to review the website (please action this right away, and then action everything else in this message)

**Follow-up:**

> Ok i missed the second half of this prompt - we may need to refresh and update this website
>
> The HTML needs to be easy to grade - there shouldbe a clear heading for each of the checks I mentioned above, a screenshot (Italked about this) - and 1-2 sentences on what the screenshot provides/proves/shows
>
> The screenshot images should go in output/app_check_images/ and link them from app_check.html with relevant path names (ex: app_check_images/inventory.png)

[Needed because I had left out the grading requirements: a clear heading per check, a screenshot, a 1–2 sentence caption, and images saved in output/app_check_images/ with descriptive names.]

**Follow-up:**

> Ok the images look good, but there are not displaing in the html link you sent me in the claude browser (its like the image error sign with the image description language) - also the buttons at the top were not nvagiating to the individual checks for me)

[Needed because the screenshots showed as broken images and the section buttons didn't jump to each check when I opened the page in the Claude viewer.]

**Follow-up:**

> Ok this looks great. roblem 11 complete.

[Needed to confirm the app check page worked after the fixes and to close out Problem 11.]


---

## Problem 12: Audit Trail, Safety, and Finishing the Harness

**Prompt:**

> on to problem 12 - Audit trail, safety, finish harness
>
> We need a append -only output/audit_trail.json file of the agent loop activity (time, tool name, short args/result, stop reason if one) do not wipe it clean between runs, but rather log it cumulatively over time without deleting.
>
> Ok we need to add some safety features. Can you add some safety features to prompts/prompt.md - please write any/all typical saftey features. Can you also add the below
>
> * do not message or email a customer proactively. You may interact with them through the chat, but do not rogue send an email.
> * Do not lie or tell the customer somewthing you do not know is true.
>
>
> Next we need to finsih the output/harness.md so that it is clear. this is one fo the things ill be graded on.
>
> Model fields in pdels.py and why we chose them
>
> list of tools and abilities
>
> our safety rules (from the above and all other problems as well
>
> Specs (loop limits, result caps, mdoels, how to run front + back)


---

## Problem 13: Push to GitHub and Submit the URL

**Prompt:**

> Help me prepare my homework for Problem 13: Push to GitHub and submit the URL (4 points). Follow these requirements carefully because the submission will be graded.
> Put the project code in a folder named `hw4` and push it to a public GitHub repository. The final submission on Canvas must be the repository URL that graders can open and clone. Do not prepare a ZIP file for submission.
> Required project structure
> Preserve these exact folder and file names:
>
> ```
> hw4/AI_prompts.md
> hw4/requirements.txt
> hw4/.env.example
> hw4/.gitignore
> hw4/README.md
>
> hw4/frontend/
>
> hw4/backend/main.py
> hw4/backend/agent.py
> hw4/backend/models.py
> hw4/backend/tools.py
> hw4/backend/prompts/prompt.md
>
> hw4/output/harness.md
> hw4/output/design.md
> hw4/output/usability.md
> hw4/output/app_check.html
> hw4/output/app_check_images/
> hw4/output/audit_trail.json
> ```
>
> The `frontend/` directory should contain the Vite React TypeScript app.
> The `backend/main.py` file should contain the FastAPI app, runnable from the backend directory with:
>
> ```
> uvicorn main:app --reload
> ```
>
> The agent itself consists of these four files under `backend/`:
>
> * `prompts/prompt.md`
> * `agent.py`
> * `tools.py`
> * `models.py`
>
> The `output/app_check_images/` directory should contain the screenshots linked from `output/app_check.html`.
> Files that must stay out of GitHub
> Do not commit or push:
>
> * The real `.env` file.
> * `campus_customs.db`.
> * The product images.
>
> Use `.gitignore` to exclude these files. Include a committed `.env.example` containing placeholders only, without real credentials or secrets.
> The data pack must remain local and outside Git tracking. Its structure is:
>
> ```
> data/campus_customs.db
> data/products/
> ```
>
> The `data/products/` directory contains the images referenced by the catalogue. These local product images are separate from the required app-check screenshots in `output/app_check_images/`.
> README requirements
> Write `hw4/README.md` so a grader can understand where to place the local data pack and how to run both the frontend and backend after placing it.
> Final verification and handoff
> Before pushing, check that the required structure is present, `.env.example` contains only placeholders, and the real `.env`, database, and product images are excluded from Git.
> After pushing, provide the public GitHub repository URL that I should submit on Canvas.
