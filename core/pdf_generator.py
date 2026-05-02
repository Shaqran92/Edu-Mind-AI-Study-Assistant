# core/pdf_generator.py
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("pdf_generator")

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib.colors import HexColor
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not available - PDF export disabled")

def create_study_guide_pdf(file_path: str, data: dict):
    """
    Generates a structured PDF study guide from processed data.
    """
    if not HAS_REPORTLAB:
        logger.error("reportlab is not installed. Cannot generate PDF.")
        return False

    try:
        doc = SimpleDocTemplate(file_path, pagesize=(8.5*inch, 11*inch), topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        # --- Custom Colors and Styles ---
        primary_color = HexColor("#667eea")
        text_color = HexColor("#2d3748")
        
        title_style = ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=26, textColor=primary_color, alignment=TA_CENTER, spaceAfter=20)
        subtitle_style = ParagraphStyle(name='SubtitleStyle', fontName='Helvetica', fontSize=12, textColor=HexColor("#718096"), alignment=TA_CENTER, spaceAfter=40)
        heading_style = ParagraphStyle(name='HeadingStyle', fontName='Helvetica-Bold', fontSize=18, textColor=primary_color, spaceBefore=20, spaceAfter=10, borderLeftColor=primary_color, borderLeftWidth=3, paddingLeft=10)
        body_style = ParagraphStyle(name='BodyStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12, textColor=text_color)
        bullet_style = ParagraphStyle(name='BulletStyle', parent=body_style, leftIndent=20, bulletIndent=10)
        question_style = ParagraphStyle(name='QuestionStyle', parent=body_style, fontName='Helvetica-Bold', spaceBefore=15)
        option_style = ParagraphStyle(name='OptionStyle', parent=body_style, leftIndent=20)
        
        story = []

        # 1. Title Page
        story.append(Paragraph(data.get('title', 'EduMind Study Guide'), title_style))
        story.append(Paragraph(f"AI-Generated Study Guide | Created: {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
        story.append(Paragraph("This document was created by the EduMind AI Study Assistant to help you learn faster and more effectively.", body_style))
        story.append(PageBreak())

        # 2. AI Summary & Key Points
        if data.get('summary'):
            story.append(Paragraph("📝 AI-Generated Summary", heading_style))
            summary_text = data['summary'].replace('\n\n', '<br/><br/>').replace('## ', '<b>').replace('**', '<b>')
            story.append(Paragraph(summary_text, body_style))

        if data.get('key_points'):
            story.append(Paragraph("🎯 Key Points", heading_style))
            for point in data['key_points']:
                story.append(Paragraph(f"• {point}", bullet_style))

        # 3. Concept Map
        if data.get('concept_map_path') and os.path.exists(data['concept_map_path']):
            story.append(PageBreak())
            story.append(Paragraph("🗺️ Concept Map", heading_style))
            story.append(Paragraph("This visual map connects the main ideas from your notes.", body_style))
            try:
                story.append(Image(data['concept_map_path'], width=7*inch, height=5.25*inch, kind='proportional'))
            except Exception as e:
                story.append(Paragraph(f"<i>[Error loading image: {e}]</i>", body_style))

        # 4. Practice Quiz
        if data.get('quiz'):
            story.append(PageBreak())
            story.append(Paragraph("❓ Practice Quiz", heading_style))
            for i, q in enumerate(data['quiz'], 1):
                story.append(Paragraph(f"{i}. {q['question']}", question_style))
                for opt in q['options']:
                    story.append(Paragraph(opt, option_style))
                story.append(Spacer(1, 0.1 * inch))
            
            # Answer Key on a new page
            story.append(PageBreak())
            story.append(Paragraph("✅ Quiz Answer Key", heading_style))
            for i, q in enumerate(data['quiz'], 1):
                story.append(Paragraph(f"<b>Question {i}: {q['answer']}</b>", body_style))
                story.append(Paragraph(f"<i>Explanation: {q['explanation']}</i>", bullet_style))

        doc.build(story)
        return True
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False