const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, LevelFormat,
  TabStopType, TabStopPosition, ExternalHyperlink, HeadingLevel
} = require("docx");
const fs = require("fs");

const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const outPath = process.argv[3] || "CV_Output.docx";

const PAGE_WIDTH = 11906;
const MARGIN = 1000;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

const ACCENT = "1A5276";
const DARK = "1C1C1C";
const MID = "444444";
const LIGHT = "777777";
const RULE_COLOR = "AED6F1";

function rule() {
  return new Paragraph({
    paragraph: {},
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 }
    },
    spacing: { before: 120, after: 80 }
  });
}

function sectionHeading(text) {
  return new Paragraph({
    children: [
      new TextRun({
        text: text.toUpperCase(),
        bold: true,
        size: 22,
        color: ACCENT,
        font: "Arial"
      })
    ],
    spacing: { before: 240, after: 60 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 }
    }
  });
}

function bulletPara(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, size: 20, color: DARK, font: "Arial" })],
    spacing: { before: 20, after: 20 }
  });
}

function spacer(before = 0) {
  return new Paragraph({ children: [], spacing: { before, after: 0 } });
}

const info = data.personal;

const children = [];

children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 40 },
    children: [
      new TextRun({
        text: info.name,
        bold: true,
        size: 52,
        color: DARK,
        font: "Arial"
      })
    ]
  })
);

children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 40 },
    children: [
      new TextRun({
        text: data.role_title || "Backend Developer",
        size: 24,
        color: ACCENT,
        font: "Arial"
      })
    ]
  })
);

children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 20 },
    children: [
      new TextRun({ text: info.email, size: 19, color: MID, font: "Arial" }),
      new TextRun({ text: "   |   ", size: 19, color: LIGHT, font: "Arial" }),
      new TextRun({ text: info.phone, size: 19, color: MID, font: "Arial" }),
      new TextRun({ text: "   |   ", size: 19, color: LIGHT, font: "Arial" }),
      new TextRun({ text: info.location, size: 19, color: MID, font: "Arial" })
    ]
  })
);

children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 60 },
    children: [
      new ExternalHyperlink({
        link: info.linkedin,
        children: [new TextRun({ text: "LinkedIn", size: 18, color: ACCENT, font: "Arial", underline: {} })]
      }),
      new TextRun({ text: "   |   ", size: 18, color: LIGHT, font: "Arial" }),
      new ExternalHyperlink({
        link: info.github,
        children: [new TextRun({ text: "GitHub", size: 18, color: ACCENT, font: "Arial", underline: {} })]
      }),
      ...(info.portfolio ? [
        new TextRun({ text: "   |   ", size: 18, color: LIGHT, font: "Arial" }),
        new ExternalHyperlink({
          link: info.portfolio,
          children: [new TextRun({ text: "Portfolio", size: 18, color: ACCENT, font: "Arial", underline: {} })]
        })
      ] : [])
    ]
  })
);

children.push(sectionHeading("Professional Summary"));
children.push(
  new Paragraph({
    children: [new TextRun({ text: data.summary, size: 20, color: DARK, font: "Arial" })],
    spacing: { before: 80, after: 80 }
  })
);

children.push(sectionHeading("Experience"));

for (const exp of data.experience) {
  children.push(
    new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }],
      spacing: { before: 120, after: 20 },
      children: [
        new TextRun({ text: exp.title, bold: true, size: 22, color: DARK, font: "Arial" }),
        new TextRun({ text: "\t", size: 20, font: "Arial" }),
        new TextRun({ text: `${exp.start} \u2013 ${exp.end}`, size: 19, color: LIGHT, font: "Arial" })
      ]
    })
  );
  children.push(
    new Paragraph({
      spacing: { before: 0, after: 40 },
      children: [
        new TextRun({ text: exp.company, size: 20, color: ACCENT, bold: true, font: "Arial" }),
        exp.type ? new TextRun({ text: `  \u00B7  ${exp.type}`, size: 19, color: LIGHT, font: "Arial" }) : new TextRun("")
      ]
    })
  );
  for (const b of exp.bullets) {
    children.push(bulletPara(b));
  }
}

if (data.projects && data.projects.length > 0) {
children.push(sectionHeading("Projects"));

for (const proj of data.projects) {
  children.push(
    new Paragraph({
      spacing: { before: 120, after: 20 },
      children: [
        new TextRun({ text: proj.name, bold: true, size: 21, color: DARK, font: "Arial" }),
        proj.link ? new TextRun({ text: `  \u2014  `, size: 18, color: LIGHT, font: "Arial" }) : new TextRun(""),
        ...(proj.link ? [
          new ExternalHyperlink({
            link: proj.link,
            children: [new TextRun({ text: proj.link, size: 18, color: ACCENT, font: "Arial", underline: {} })]
          })
        ] : [])
      ]
    })
  );
  children.push(
    new Paragraph({
      spacing: { before: 0, after: 20 },
      children: [
        new TextRun({ text: "Tech: ", bold: true, size: 19, color: MID, font: "Arial" }),
        new TextRun({ text: proj.tech.join(", "), size: 19, color: MID, font: "Arial" })
      ]
    })
  );
  children.push(
    new Paragraph({
      spacing: { before: 0, after: 60 },
      children: [new TextRun({ text: proj.description, size: 19, color: DARK, font: "Arial" })]
    })
  );
}
}

children.push(sectionHeading("Skills"));

const skills = data.skills;
const skillRows = [
  ["Languages", skills.languages ? skills.languages.join(", ") : ""],
  ["Frameworks", skills.frameworks ? skills.frameworks.join(", ") : ""],
  ["Databases", skills.databases ? skills.databases.join(", ") : ""],
  ["Tools", skills.tools ? skills.tools.join(", ") : ""],
  ["Concepts", skills.concepts ? skills.concepts.join(", ") : ""]
].filter(([, v]) => v);

for (const [label, value] of skillRows) {
  children.push(
    new Paragraph({
      spacing: { before: 60, after: 30 },
      children: [
        new TextRun({ text: `${label}: `, bold: true, size: 20, color: DARK, font: "Arial" }),
        new TextRun({ text: value, size: 20, color: MID, font: "Arial" })
      ]
    })
  );
}

children.push(sectionHeading("Education"));

for (const edu of data.education) {
  children.push(
    new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }],
      spacing: { before: 100, after: 20 },
      children: [
        new TextRun({ text: `${edu.degree} \u2014 ${edu.field}`, bold: true, size: 21, color: DARK, font: "Arial" }),
        new TextRun({ text: "\t", size: 20, font: "Arial" }),
        new TextRun({ text: edu.year || "", size: 19, color: LIGHT, font: "Arial" })
      ]
    })
  );
  children.push(
    new Paragraph({
      spacing: { before: 0, after: 60 },
      children: [
        new TextRun({ text: edu.institution, size: 20, color: ACCENT, font: "Arial" }),
        new TextRun({ text: `  \u00B7  ${edu.status || ""}`, size: 19, color: LIGHT, font: "Arial" })
      ]
    })
  );
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: { indent: { left: 440, hanging: 260 } }
          }
        }]
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_WIDTH, height: 16838 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
      }
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log("Saved: " + outPath);
});
