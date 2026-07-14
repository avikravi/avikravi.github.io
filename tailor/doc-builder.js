// Expects a global `docx` object (loaded via CDN in the browser) with:
// Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle
// In Node (for testing only) this is provided via require('docx').

function getDocxLib() {
  if (typeof docx !== "undefined") return docx;
  return require("docx");
}

const FONT = "Calibri";
const NAME_SIZE = 28, CONTACT_SIZE = 18, SECTION_SIZE = 20, BODY_SIZE = 20;

function buildResumeDoc(masterData, selectedEntries, companyName, roleTitle) {
  const { Document, Paragraph, TextRun, AlignmentType, BorderStyle } = getDocxLib();
  const c = masterData.contact;

  function contactLine() {
    return new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({
        text: `${c.location} | ${c.phone} | ${c.email} | ${c.linkedin.replace("https://www.", "")} | ${c.github_io}`,
        size: CONTACT_SIZE, font: FONT,
      })],
    });
  }

  function sectionHeader(text) {
    return new Paragraph({
      spacing: { before: 200, after: 80 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "000000" } },
      children: [new TextRun({ text, bold: true, size: SECTION_SIZE, font: FONT, allCaps: true })],
    });
  }

  function entryHeader(left, right) {
    return new Paragraph({
      spacing: { before: 100, after: 20 },
      tabStops: [{ type: "right", position: 9360 }],
      children: [
        new TextRun({ text: left, bold: true, size: BODY_SIZE, font: FONT }),
        new TextRun({ text: `\t${right}`, size: BODY_SIZE, font: FONT, italics: true }),
      ],
    });
  }

  function bullet(text) {
    return new Paragraph({
      bullet: { level: 0 },
      spacing: { after: 40 },
      indent: { left: 360 },
      children: [new TextRun({ text, size: BODY_SIZE, font: FONT })],
    });
  }

  function subline(text) {
    return new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text, italics: true, size: BODY_SIZE, font: FONT })],
    });
  }

  const children = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
      children: [new TextRun({ text: c.name.replace(" (Avi)", "").toUpperCase(), bold: true, size: NAME_SIZE, font: FONT })],
    }),
    contactLine(),
    sectionHeader("Education"),
  ];

  masterData.education.forEach(ed => {
    children.push(entryHeader(`${ed.school} (${ed.location}) — ${ed.degree}`, ed.dates));
    if (ed.coursework) children.push(subline(`Coursework: ${ed.coursework.join(", ")}`));
    if (ed.teaching_assistant) children.push(subline(`Teaching Assistant, ${ed.teaching_assistant}`));
  });

  children.push(sectionHeader("Relevant Experience"));

  const SUSPICIOUS_PATTERNS = /conflict|NEEDS_|PLACEHOLDER|see .*_note|unresolved/i;

  selectedEntries.forEach(entry => {
    children.push(entryHeader(`${entry.title} — ${entry.org}`, entry.dates));
    (entry.bullets || []).forEach(b => {
      if (b.flag === "NEEDS_DETAIL" || b.flag === "NEEDS_VERIFICATION") return; // never surface unverified content
      if (SUSPICIOUS_PATTERNS.test(b.text)) {
        console.warn(`Skipped a bullet for ${entry.id} — looked like it contained internal metadata:`, b.text);
        return;
      }
      children.push(bullet(b.text));
    });
  });

  // Skills
  children.push(sectionHeader("Skills"));
  const allSkills = new Set();
  selectedEntries.forEach(e => (e.skills || []).forEach(s => allSkills.add(s)));
  children.push(new Paragraph({
    spacing: { after: 20 },
    children: [new TextRun({ text: Array.from(allSkills).join(", "), size: BODY_SIZE, font: FONT })],
  }));

  return new Document({
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 720, bottom: 720, left: 720, right: 720 } } },
      children,
    }],
  });
}

function buildCoverLetterDoc(masterData, selectedEntries, companyName, roleTitle) {
  const { Document, Paragraph, TextRun } = getDocxLib();
  const c = masterData.contact;
  const BODY = 22;

  function para(text) {
    return new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text, size: BODY, font: FONT })] });
  }

  const top = selectedEntries.slice(0, 2);
  const bulletMentions = top.map(e => {
    const firstBullet = (e.bullets || []).find(b => !b.flag);
    return firstBullet ? `As ${e.title} at ${e.org}, I ${firstBullet.text.charAt(0).toLowerCase() + firstBullet.text.slice(1)}` : null;
  }).filter(Boolean);

  const children = [
    new Paragraph({ children: [new TextRun({ text: c.name.replace(" (Avi)", ""), bold: true, size: BODY, font: FONT })], spacing: { after: 20 } }),
    new Paragraph({ children: [new TextRun({ text: `${c.location} | ${c.phone} | ${c.email}`, size: BODY, font: FONT })], spacing: { after: 400 } }),
    para(`Dear ${companyName} Hiring Team,`),
    para(`I'm writing to apply for the ${roleTitle} role at ${companyName}. My background combines a Master's in Data Science at Rice University with hands-on product and technical experience across several startups and internships.`),
  ];
  bulletMentions.forEach(m => children.push(para(m)));
  children.push(para(`I'd welcome the chance to discuss how I could contribute to your team. Thank you for your consideration.`));
  children.push(para("Sincerely,"));
  children.push(para(c.name.replace(" (Avi)", "")));

  return new Document({
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children,
    }],
  });
}

if (typeof module !== "undefined") {
  module.exports = { buildResumeDoc, buildCoverLetterDoc };
}
