// Reuses tokenize() from matching-engine.js — load that first.

function buildResumeCorpusText(masterData, includeBlackSwan) {
  const parts = [];
  masterData.education.forEach(ed => {
    parts.push(ed.degree, ed.school);
    (ed.coursework || []).forEach(c => parts.push(c));
    (ed.activities_and_coursework || []).forEach(c => parts.push(c));
    if (ed.teaching_assistant) parts.push(ed.teaching_assistant);
  });
  masterData.experience.forEach(e => {
    if (e.id === "blackswan_marketing" && !includeBlackSwan) return;
    parts.push(e.title, e.org, e.tagline || "");
    (e.industry_tags || []).forEach(t => parts.push(t));
    (e.skills || []).forEach(s => parts.push(s));
    (e.bullets || []).forEach(b => {
      if (b.flag) return; // don't let unverified bullets influence the score either
      parts.push(b.text);
    });
  });
  (masterData.side_projects_and_ventures || []).forEach(p => {
    parts.push(p.name, p.description || "");
    (p.industry_tags || []).forEach(t => parts.push(t));
  });
  return parts.join(" ");
}

function termFrequencyVector(tokens) {
  const vec = {};
  tokens.forEach(t => { vec[t] = (vec[t] || 0) + 1; });
  return vec;
}

function cosineSimilarity(vecA, vecB) {
  const allTerms = new Set([...Object.keys(vecA), ...Object.keys(vecB)]);
  let dot = 0, magA = 0, magB = 0;
  allTerms.forEach(term => {
    const a = vecA[term] || 0;
    const b = vecB[term] || 0;
    dot += a * b;
    magA += a * a;
    magB += b * b;
  });
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

// Combines raw text cosine similarity with the structured tag/skill overlap
// already used for entry selection, since tag overlap is a stronger signal
// than raw word frequency (a JD saying "computer vision" once should count
// more than a resume repeating "product" ten times).
function computeMatchScore(masterData, jdText) {
  const includeBlackSwan = shouldIncludeBlackSwan(jdText);
  const resumeText = buildResumeCorpusText(masterData, includeBlackSwan);

  const jdTokens = tokenize(jdText);
  const resumeTokens = tokenize(resumeText);

  const cosine = cosineSimilarity(termFrequencyVector(jdTokens), termFrequencyVector(resumeTokens));

  // Structured score: how much of the JD's vocabulary is covered by tag/skill bags,
  // reusing the same scoring function used for entry selection.
  const jdTokenCounts = countTokens(jdTokens);
  const candidates = masterData.experience.filter(e => includeBlackSwan || e.id !== "blackswan_marketing");
  const structuredRaw = candidates.reduce((sum, e) => sum + scoreEntry(e, jdTokenCounts), 0);
  const jdUniqueTerms = new Set(jdTokens).size || 1;
  const structuredNormalized = Math.min(1, structuredRaw / (jdUniqueTerms * 1.5));

  // Blend: structured tag/skill overlap weighted higher than raw word-frequency cosine,
  // then scaled empirically so scores land in an intuitive range.
  const blended = (structuredNormalized * 0.7) + (cosine * 0.3);
  const scaled = Math.round(Math.min(100, blended * 140));

  return { score: scaled, cosine: Math.round(cosine * 1000) / 1000, structured: Math.round(structuredNormalized * 1000) / 1000 };
}

if (typeof module !== "undefined") {
  module.exports = { computeMatchScore, buildResumeCorpusText, cosineSimilarity, termFrequencyVector };
}
