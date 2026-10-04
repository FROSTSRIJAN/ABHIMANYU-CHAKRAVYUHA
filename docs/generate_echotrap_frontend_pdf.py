from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

out_path = r"C:\Users\ananya\Desktop\Projects\ABHIMANYU-CHAKRAVYUHA\docs\echotrap_frontend_navbar_spec.pdf"

doc = SimpleDocTemplate(out_path, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=40, bottomMargin=40)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Header', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#0B3D4A'), leading=24, spaceAfter=12))
styles.add(ParagraphStyle(name='Subhead', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2A2A2A'), leading=16, spaceAfter=8))
styles.add(ParagraphStyle(name='Bullet', fontName='Helvetica', fontSize=10.5, textColor=colors.HexColor('#1d1d1d'), leading=16, leftIndent=18, spaceAfter=4))
styles.add(ParagraphStyle(name='Note', fontName='Helvetica-Oblique', fontSize=9.5, textColor=colors.HexColor('#5a5a5a'), leading=14, spaceAfter=10))

story = []

story.append(Paragraph('EchoTrap Frontend Navbar + Multi-Page Blueprint', styles['Header']))
story.append(Paragraph('Investor-safety claim mutation intelligence dashboard', styles['Subhead']))
story.append(Paragraph('This document describes a clean multi-page frontend for the EchoTrap product. The app supports sequence analysis, mutation detection, explainability, and safety-first interpretation.', styles['Bullet']))
story.append(Paragraph('Core product goals:', styles['Subhead']))
story.append(ListFlowable([
    ListItem(Paragraph('Let the user compare 2–5 related messages in order.', styles['Bullet'])),
    ListItem(Paragraph('Detect certainty escalation, urgency pressure, and persuasion language.', styles['Bullet'])),
    ListItem(Paragraph('Explain the result in simple language without implying fraud proof.', styles['Bullet'])),
    ListItem(Paragraph('Present a professional investor-protection dashboard with strong safety cues.', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))
story.append(PageBreak())

story.append(Paragraph('Navigation Structure', styles['Header']))
story.append(Paragraph('Persistent top navbar with page-based routing', styles['Subhead']))
story.append(Paragraph('Navbar layout:', styles['Subhead']))
story.append(Paragraph('Left: Brand + EchoTrap | Right: Home, Analyzer, Results, Safety, Diagnostics, Docs | Top-right: EN / हिं toggle | Mobile: hamburger menu', styles['Bullet']))
story.append(Paragraph('Recommended route map:', styles['Subhead']))
story.append(ListFlowable([
    ListItem(Paragraph('/ -> Home', styles['Bullet'])),
    ListItem(Paragraph('/analyze -> Analyzer', styles['Bullet'])),
    ListItem(Paragraph('/processing -> Processing', styles['Bullet'])),
    ListItem(Paragraph('/results -> Results', styles['Bullet'])),
    ListItem(Paragraph('/safety -> Safety Guide', styles['Bullet'])),
    ListItem(Paragraph('/diagnostics -> Diagnostics', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))
story.append(PageBreak())

story.append(Paragraph('Page-by-Page UI Blueprint', styles['Header']))
story.append(Paragraph('1. Landing page', styles['Subhead']))
story.append(ListFlowable([
    ListItem(Paragraph('Hero banner with product value proposition and CTA.', styles['Bullet'])),
    ListItem(Paragraph('Why EchoTrap section with three trust-building features.', styles['Bullet'])),
    ListItem(Paragraph('Example sequence visual showing message mutation.', styles['Bullet'])),
    ListItem(Paragraph('Privacy and safety note.', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))

story.append(Paragraph('2. Analyzer page', styles['Subhead']))
story.append(ListFlowable([
    ListItem(Paragraph('2–5 message cards in order from earliest to latest.', styles['Bullet'])),
    ListItem(Paragraph('Add/remove controls and validation warnings.', styles['Bullet'])),
    ListItem(Paragraph('Demo sequence load button.', styles['Bullet'])),
    ListItem(Paragraph('Run Mutation Analysis CTA.', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))

story.append(Paragraph('3. Results page', styles['Subhead']))
story.append(ListFlowable([
    ListItem(Paragraph('Summary banner with overall status and caution note.', styles['Bullet'])),
    ListItem(Paragraph('Claim evolution timeline with highlighted risky phrases.', styles['Bullet'])),
    ListItem(Paragraph('Mutation cards and signal cards for semantic continuity, certainty shift, urgency, and guarantee language.', styles['Bullet'])),
    ListItem(Paragraph('Plain-language explanation + safety guidance section.', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))
story.append(PageBreak())

story.append(Paragraph('Visual style and interaction rules', styles['Header']))
story.append(ListFlowable([
    ListItem(Paragraph('Dark background with strong contrast and readable typography.', styles['Bullet'])),
    ListItem(Paragraph('Use neutral / watch / strong colors for risk state.', styles['Bullet'])),
    ListItem(Paragraph('Keep the language cautious: warning, not fraud proof.', styles['Bullet'])),
    ListItem(Paragraph('Use accessible spacing and mobile-first layout cards.', styles['Bullet'])),
    ListItem(Paragraph('Display a visible disclaimer near all analysis results.', styles['Bullet'])),
    ListItem(Paragraph('Support EN / हिं language switching for the explanation panel.', styles['Bullet'])),
], bulletType='bullet', bulletFontName='Helvetica', leftIndent=20))

story.append(Paragraph('UI implementation recommendation', styles['Subhead']))
story.append(Paragraph('Use React + TypeScript + Vite, a shared top-level navbar component, and route-based page layouts. Keep the backend response contract stable so the UI can render real analysis values cleanly.', styles['Bullet']))
story.append(Paragraph('This frontend should honestly reflect the actual backend pipeline: semantic similarity, mutation detection, verification status, and explanation output.', styles['Note']))

doc.build(story)
print(f'Created PDF: {out_path}')
