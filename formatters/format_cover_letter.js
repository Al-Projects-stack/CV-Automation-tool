const {
  Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, ExternalHyperlink
} = require("docx");
const fs = require("fs");

const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const outPath = process.argv[3] || "CoverLetter_Output.docx";

const DARK = "1C1C1C";
const MID = "444444";
const LIGHT = "777777";
const ACCENT = "1A5276";

const paragraphs = data.cover_letter.trim().split(/\n\n+/);

const children = [];

children.push(
  new Paragraph({
    spacing: { before: 0, after: 20 },
    children: [
      new TextRun({ text: data.name, bold: true, size: 26, color: DARK, font: "Arial" })
    ]
  })
);

children.push(
  new Paragraph({
    spacing: { before: 0, after: 20 },
    children: [
      new TextRun({ text: data.email, size: 20, color: MID, font: "Arial" }),
      new TextRun({ text: "   |   ", size: 20, color: LIGHT, font: "Arial" }),
      new TextRun({ text: data.phone, size: 20, color: MID, font: "Arial" }),
      new TextRun({ text: "   |   ", size: 20, color: LIGHT, font: "Arial" }),
      new TextRun({ text: data.location, size: 20, color: MID, font: "Arial" })
    ]
  })
);

children.push(
  new Paragraph({
    spacing: { before: 0, after: 60 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 }
    },
    children: []
  })
);

children.push(
  new Paragraph({
    spacing: { before: 300, after: 80 },
    children: [
      new TextRun({ text: data.date, size: 20, color: LIGHT, font: "Arial" })
    ]
  })
);

children.push(
  new Paragraph({
    spacing: { before: 80, after: 60 },
    children: [
      new TextRun({ text: "Dear Hiring Manager,", size: 21, color: DARK, font: "Arial" })
    ]
  })
);

for (const para of paragraphs) {
  if (para.trim()) {
    children.push(
      new Paragraph({
        spacing: { before: 0, after: 180 },
        children: [
          new TextRun({ text: para.trim(), size: 21, color: DARK, font: "Arial" })
        ]
      })
    );
  }
}

children.push(
  new Paragraph({
    spacing: { before: 120, after: 20 },
    children: [
      new TextRun({ text: "Regards,", size: 21, color: DARK, font: "Arial" })
    ]
  })
);

children.push(
  new Paragraph({
    spacing: { before: 0, after: 0 },
    children: [
      new TextRun({ text: data.name, bold: true, size: 21, color: DARK, font: "Arial" })
    ]
  })
);

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("Saved: " + outPath);
});
