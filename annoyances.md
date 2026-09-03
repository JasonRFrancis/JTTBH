# JTTBH Annoyances

## Design and Layout

## Admin

## Dashboard
 [ ] The habits dashboard should also provide a summary of streak or trend data
 [x] Todo, chores, fitness, and study should also appear on the dashboard

## Todo
 [x] Todo is a bit of a mess. When adding a todo at the bottom of the list, a new temporary todo item is appended to the end of the list with every keystroke
 [x] I should be able to drag todos to other lists. I should also be able to assign them from the `…` menu
 [x] The input form should use the same typeface and the same size as the displayed todo. Editing the todo should be a minimalist experience
 [x] I don't want to see the checkbox. The todo should be crossed out if the checkbox is checked — click to toggle; double-click title to edit
 [x] Undone todos from previous days should move straight to the `Someday Soon` list on page load — no one-day grace period in the daily list first

## Habits

## Projects

## Bookmarks
 [x] The bookmarklet window is the wrong size. I don't want to have to scroll to push the submit button
 [x] Autocomplete in my browser is trying to add spaces to the tags. I would like that to not happen. Remove spaces from the tags if they appear
 [x] Instead of the tags being comma separated, present them as separate UI elements. When I hit space or some stop punctuation, separate out the tag
 [x] I think I need a Read Later bookmark that skips the form and just adds it to the Read Later list
 [ ] The bookmarks page should be better organized. I would like it to be cards-based with a much higher information density
 [x] The default view should be anything saved in the last 24 hours, grouped by bookmark type: videos, read later, etc. Anything that is favorited should show up there, too
 [x] I would like and AI summary of the page linked to by the bookmark. A 1-sentence, a 3-sentence, and a 2-paragraph summary should be provided
 [ ] For any favorites, I should be able to indicate whether or not to check for updated information. There should be a cron job or some other way to periodically poll the page and indicate when it was last updated. Then track the timestamp when I click on the link

## Fitness
 [ ] The data model for exercises should be more flexible. It makes sense to track different information about different exercises
 [ ] I should be able to customize the input form that shows up when I add a set. Something like `Setup: [setup] Reps: [reps] Weight: [weight] [notes]` should produce a form with those inputs
 [ ] On the iPhone, after I have recorded a set, if I shake my phone, I get an option to undo what I typed. I would like to somehow disable that
 [x] I only record my weight certain days. I would like to be able to indicate when that shows up
 [x] I would like a view where I can see trends and my progress. I should be able to add a note without recording a set

## Triage

## Chores
 [x] If I am not currently part of a household, the system should create one for me. If I invite someone to join my household, it should give them an option to merge theirs with mine or abandon theirs

## Media
 [ ] The information should be more densely presented. Use cards. I should see at a glance what media I would like to consume. I should be able to reorder and prioritize what comes next
 [ ] Shows should track episode information. I should be able to mark off which episodes I have watched. When a new episode is released, I should see an indication of that as well as an indication (and a link) to which streaming service offers that show

## Journal

## Study
 [x] Music uses the Accompaniment mp3 instead of the Vocal
 [x] Overcast is not downloading all the "episodes" for the day's study
 [x] The podcast feed appears in random order — items now get staggered pubDates so podcast apps display them in feed order
 [x] The podcast feed has the talk title, but I would like the speaker and the context to be represented, too — title is now "Author: Title"; subtitle/category added as itunes:subtitle
 [x] The podcast feed needs album artwork — needs an image file added to static/ first
 [x] I want to reorder the Study collections on my page
 [x] When adding a new subscription, the name is ignored. The name input hint should be specific to the collection, too
 [x] The collection `Subsciption Name` on the form is not prefilled
 [ ] I don't like the schema for the `study_` tables. The `study_collection` table should have a title, subtitle, etc. The `study_item` table should only have information unique to the item
 [ ] There may be more mp3 files than have been found so far, especially with the Hebrew texts

## Quotes
 [x] The tags are more important to me than the individual quotes. I should be able to select a category and see quotes related to that topic
 [x] Pre-seed the tags from the categories on `https://www.churchofjesuschrist.org/study/manual/gospel-principles?lang=eng`. If I start typing a tag, give me the chance to select an existing one
 [x] Instead of the tags being comma separated, present them as separate UI elements. When I hit space or some stop punctuation, separate out the tag

## Recipes

## Appointments