// ---------- Text utilities ----------
const STOPWORDS = new Set(("a about above after again against all am an and any are aren't as at be because been before "
  + "being below between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each "
  + "few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him "
  + "himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself "
  + "no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd she'll she's "
  + "should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd "
  + "they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were "
  + "weren't what what's when when's where where's which while who who's whom why why's with won't would wouldn't you "
  + "you'd you'll you're you've your yours yourself yourselves will job role team years experience work using strong "
  + "including etc within across ability able also including looking looking for you'll you're we're").split(" "));

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z0-9+#.]+/g) || [])
    .filter(w => w.length > 1 && !STOPWORDS.has(w));
}

// ---------- Scoring ----------
function entryKeywordBag(entry) {
  const bag = [];
  bag.push(...tokenize(entry.title || ""));
  bag.push(...tokenize(entry.org || ""));
  bag.push(...tokenize(entry.tagline || ""));
  (entry.industry_tags || []).forEach(t => bag.push(...tokenize(t)));
  (entry.skills || []).forEach(s => bag.push(...tokenize(s)));
  return bag;
}

function scoreEntry(entry, jdTokenCounts) {
  const bag = entryKeywordBag(entry);
  const bagSet = new Set(bag);
  let score = 0;
  bagSet.forEach(word => {
    if (jdTokenCounts[word]) {
      // industry_tags words count double — they're the strongest relevance signal
      const isIndustryTag = (entry.industry_tags || []).some(t => tokenize(t).includes(word));
      score += jdTokenCounts[word] * (isIndustryTag ? 2 : 1);
    }
  });
  return score;
}

function countTokens(tokens) {
  const counts = {};
  tokens.forEach(t => { counts[t] = (counts[t] || 0) + 1; });
  return counts;
}

const BLACKSWAN_TRIGGER_WORDS = ["marketing", "sales", "retail", "brick-and-mortar", "storefront", "studio",
  "in-person", "customer-facing", "physical location", "brick and mortar", "franchise", "wellness"];

function shouldIncludeBlackSwan(jdText) {
  const lower = jdText.toLowerCase();
  return BLACKSWAN_TRIGGER_WORDS.some(w => lower.includes(w));
}

function selectEntries(masterData, jdText, maxEntries = 5) {
  const jdTokens = tokenize(jdText);
  const jdTokenCounts = countTokens(jdTokens);

  const candidates = masterData.experience.filter(e => e.id !== "blackswan_marketing");
  const scored = candidates.map(e => ({ entry: e, score: scoreEntry(e, jdTokenCounts) }));
  scored.sort((a, b) => b.score - a.score);

  let selected = scored.filter(s => s.score > 0).slice(0, maxEntries).map(s => s.entry);

  // Fallback: if nothing scored (JD too generic / no keyword overlap), use the most recent roles
  if (selected.length === 0) {
    selected = masterData.experience.filter(e => e.id !== "blackswan_marketing").slice(0, 3);
  }

  if (shouldIncludeBlackSwan(jdText)) {
    const bs = masterData.experience.find(e => e.id === "blackswan_marketing");
    if (bs) selected.push(bs);
  }

  return selected;
}

if (typeof module !== "undefined") {
  module.exports = { tokenize, scoreEntry, selectEntries, shouldIncludeBlackSwan, countTokens };
}
