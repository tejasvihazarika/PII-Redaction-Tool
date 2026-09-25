import { Document, Packer, Paragraph, TextRun, HeadingLevel } from "docx";

export async function exportToDocx(redactedText, filename = "redacted_document.docx") {
  const lines = redactedText.split("\n");
  
  const children = [
    new Paragraph({
      text: "Redactly - Redacted Document",
      heading: HeadingLevel.HEADING_1,
      spacing: { after: 200 }
    })
  ];

  lines.forEach(line => {
    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: line,
            font: "Calibri",
            size: 22
          })
        ],
        spacing: { after: 100 }
      })
    );
  });

  const doc = new Document({
    sections: [
      {
        properties: {},
        children
      }
    ]
  });

  const blob = await Packer.toBlob(doc);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
