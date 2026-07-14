// Requires: docx (global, loaded via CDN), matching-engine.js, doc-builder.js — all loaded before this script.

let MASTER_DATA = null;

async function loadMasterData() {
  if (MASTER_DATA) return MASTER_DATA;
  const res = await fetch("master_resume_data.json", { cache: "no-store" });
  MASTER_DATA = await res.json();
  return MASTER_DATA;
}

function slugifyFilename(text) {
  return (text || "").replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "");
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

async function handleGenerateClick() {
  const companyInput = document.getElementById("tailorCompany");
  const roleInput = document.getElementById("tailorRole");
  const jdInput = document.getElementById("tailorJD");
  const statusEl = document.getElementById("tailorStatus");
  const button = document.getElementById("tailorGenerateBtn");

  const company = companyInput.value.trim();
  const role = roleInput.value.trim();
  const jdText = jdInput.value.trim();

  if (!company || !role || !jdText) {
    statusEl.textContent = "Please fill in company, role, and the job description before generating.";
    statusEl.style.color = "var(--danger, #ff4d5e)";
    return;
  }

  button.disabled = true;
  statusEl.style.color = "var(--text-dim)";
  statusEl.textContent = "Loading resume data...";

  try {
    const masterData = await loadMasterData();

    statusEl.textContent = "Matching your experience to this job description...";
    const selected = selectEntries(masterData, jdText);

    statusEl.textContent = `Selected: ${selected.map(e => e.title + " @ " + e.org).join(", ")}. Building documents...`;

    const resumeDoc = buildResumeDoc(masterData, selected, company, role);
    const coverDoc = buildCoverLetterDoc(masterData, selected, company, role);

    const [resumeBlob, coverBlob] = await Promise.all([
      docx.Packer.toBlob(resumeDoc),
      docx.Packer.toBlob(coverDoc),
    ]);

    const slug = slugifyFilename(company) + "_" + slugifyFilename(role);
    triggerDownload(resumeBlob, `${slug}_Resume.docx`);
    triggerDownload(coverBlob, `${slug}_CoverLetter.docx`);

    statusEl.style.color = "var(--neon-blue, #00f5ff)";
    statusEl.textContent = `Done — ${slug}_Resume.docx and ${slug}_CoverLetter.docx should be in your Downloads folder. Selected experience: ${selected.map(e => e.title + " @ " + e.org).join(", ")}.`;
  } catch (err) {
    console.error(err);
    statusEl.style.color = "var(--danger, #ff4d5e)";
    statusEl.textContent = "Something went wrong generating the documents — check the browser console for details.";
  } finally {
    button.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("tailorGenerateBtn");
  if (btn) btn.addEventListener("click", handleGenerateClick);
});
