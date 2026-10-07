const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, VerticalAlign, HeightRule } = require('docx');

const FONT = 'Arial';
const PINK = 'F4DCE6', DARK = 'B03A6B', LINE = '9C4A6E';
const run = (text, o = {}) => new TextRun({ text, rightToLeft: true, font: FONT,
  size: o.size || 25, sizeComplexScript: o.size || 25, bold: o.bold, boldComplexScript: o.bold,
  color: o.color, shading: o.shade ? { type: ShadingType.CLEAR, color: 'auto', fill: o.shade } : undefined });
const para = (runs, o = {}) => new Paragraph({ bidirectional: true, alignment: o.align || AlignmentType.RIGHT,
  spacing: { before: o.before || 0, after: o.after ?? 40, line: o.line || 290 }, border: o.border,
  indent: o.indent, children: runs });

const box = { style: BorderStyle.SINGLE, size: 8, color: LINE, space: 3 };
const W = 10464, COL = W / 6;
const cellBorder = { style: BorderStyle.SINGLE, size: 8, color: LINE };
const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };

const heads = ['الْإِبْداعُ التِّكْنولوجِيُّ', 'الْإِبْداعُ الْعِلْمِيُّ', 'الْإِبْداعُ الْأَدَبِيُّ',
  'الْإِبْداعُ الصِّناعِيُّ', 'الْإِبْداعُ الْحِرَفِيُّ وَالْفَنِّيُّ', 'الْإِبْداعُ اللُّغَوِيُّ'];
const ex = ['الْبَريدُ الْإِلِكْتُرونِيُّ', 'الْهَنْدَسَةُ', 'الْقِصَّةُ', 'الْمَرْكَباتُ الْكَهْرَبائِيَّةُ',
  'الرَّسْمُ', 'الْإِلْقاءُ'];

const cell = (t, o = {}) => new TableCell({ width: { size: COL, type: WidthType.DXA }, borders,
  verticalAlign: VerticalAlign.CENTER,
  shading: o.shade ? { type: ShadingType.CLEAR, color: 'auto', fill: o.shade } : undefined,
  margins: { top: 40, bottom: 40, left: 60, right: 60 },
  children: [para(t ? [run(t, { bold: o.bold, size: 24 })] : [], { align: AlignmentType.CENTER, after: 0 })] });
const row = (cells, h) => new TableRow({ height: { value: h, rule: HeightRule.ATLEAST }, children: cells });

function copy() {
  return [
    para([run(' نَشاط 2 ', { bold: true, color: 'FFFFFF', shade: DARK, size: 27 }), run('     '),
      run('تَمْييزُ أَنْواعِ الْإِبْداعِ', { bold: true, size: 30 })],
      { align: AlignmentType.CENTER, after: 80 }),
    para([run('خُطُواتُ الْعَمَلِ:', { bold: true, color: DARK })], { after: 20 }),
    para([run('1 ', { bold: true, color: DARK }), run('أَتَعاوَنُ مَعَ أَفْرادِ مَجْموعَتي عَلى تَصْنيفِ أَنْواعِ الْفُنونِ وَالْإِبْداعاتِ الْوارِدَةِ في الصُّنْدوقِ وَفْقَ ما يُناسِبُها في الْجَدْوَلِ (1).')], { after: 60 }),
    para([run('الْهَنْدَسَةُ - الْخَطابَةُ - الرَّسْمُ - الْإِلْقاءُ - الْبَريدُ الْإِلِكْتُرونِيُّ - الْمِصْباحُ الْكَهْرَبائِيُّ - آلاتُ الْمَسْحِ الرَّقْمِيَّةُ - الرِّواياتُ - الْمَرْكَباتُ الْكَهْرَبائِيَّةُ - النَّحْتُ - الْقِصَّةُ - التَّصْميمُ وَالْإِعْلانُ.')],
      { border: { top: box, bottom: box, left: box, right: box }, after: 100, line: 280 }),
    para([run('الْجَدْوَلُ (1): تَصْنيفُ أَنْواعِ الْفُنونِ وَالْإِبْداعاتِ حَسَبَ أَنْماطِ التَّعَلُّمِ.', { bold: true })],
      { align: AlignmentType.CENTER, after: 60 }),
    new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: Array(6).fill(COL),
      visuallyRightToLeft: true,
      rows: [row(heads.map(h => cell(h, { bold: true, shade: PINK })), 720),
             row(ex.map(e => cell(e)), 640),
             ...[0, 1, 2].map(() => row(Array(6).fill(0).map(() => cell('')), 820))] }),
    para([run('أُفَكِّرُ: ', { bold: true, color: DARK }), run('هَلِ الْإِبْداعُ فِطْرِيٌّ أَمْ مُكْتَسَبٌ؟', { bold: true })], { before: 80, after: 0 }),
  ];
}

const cut = para([run('✂', { color: '888888', size: 18 })], { align: AlignmentType.LEFT, before: 300, after: 300,
  border: { bottom: { style: BorderStyle.DASHED, size: 6, color: '888888', space: 1 } } });

const doc = new Document({
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 567, bottom: 454, left: 720, right: 720 } } },
    children: [...copy(), cut, ...copy()] }],
});
Packer.toBuffer(doc).then(b => fs.writeFileSync(process.argv[2], b));
