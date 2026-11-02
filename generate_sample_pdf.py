"""Generates guidelines/qatar_diabetes_guideline_2023_simulated.pdf — a simulated,
multi-page Qatar Diabetes Guideline used as the default demo document for the RAG
pipeline. Not an official MoPH publication; created for this portfolio project.
Run once: python _generate_sample_pdf.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

OUT_DIR = Path("guidelines")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "qatar_diabetes_guideline_2023_simulated.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=20, spaceAfter=18)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceBefore=12, spaceAfter=10)
body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=11, leading=16, spaceAfter=10)
note = ParagraphStyle("Note", parent=styles["BodyText"], fontSize=9, leading=13, textColor="#555555")

PAGES = [
    (
        "Qatar Diabetes Guideline 2023",
        title_style,
        [
            Paragraph(
                "<b>Simulated Clinical Guideline — Portfolio / Educational Use Only</b>",
                body,
            ),
            Paragraph(
                "This document is a simulated clinical guideline created for a student "
                "portfolio project (Qatar NCD Advisor). It is not an official publication "
                "of the Qatar Ministry of Public Health. Content is written to be clinically "
                "plausible and is used solely to demonstrate a retrieval-augmented generation "
                "(RAG) pipeline over a real PDF document.",
                note,
            ),
        ],
    ),
    (
        "Section 1. Diagnostic Criteria",
        h1,
        [
            Paragraph(
                "Type 2 Diabetes Mellitus (T2DM) is diagnosed when fasting plasma glucose is "
                "&ge; 126 mg/dL (7.0 mmol/L), 2-hour plasma glucose during a 75g OGTT is "
                "&ge; 200 mg/dL (11.1 mmol/L), or HbA1c is &ge; 6.5% (48 mmol/mol), confirmed "
                "on repeat testing unless the patient has unequivocal hyperglycemia symptoms.",
                body,
            ),
            Paragraph(
                "Screening is recommended for adults in Qatar aged 40 and above, and earlier "
                "for individuals with obesity, a first-degree relative with T2DM, or a history "
                "of gestational diabetes.",
                body,
            ),
        ],
    ),
    (
        "Section 2. First-line Therapy",
        h1,
        [
            Paragraph(
                "Metformin is the preferred first-line pharmacologic agent for all patients "
                "with Type 2 Diabetes unless contraindicated. Therapy should be initiated "
                "alongside structured lifestyle and dietary counselling.",
                body,
            ),
            Paragraph(
                "Metformin should be titrated gradually (e.g. starting at 500mg once or twice "
                "daily) to reduce gastrointestinal side effects, with a usual maintenance dose "
                "of 1500-2000mg per day in divided doses.",
                body,
            ),
        ],
    ),
    (
        "Section 3. Metformin Contraindications",
        h1,
        [
            Paragraph(
                "Metformin is contraindicated in patients with an eGFR below 30 mL/min/1.73m^2, "
                "severe hepatic impairment, or unstable/decompensated heart failure. Metformin "
                "should also be discontinued or avoided when gastrointestinal intolerance "
                "prevents the patient from tolerating an effective dose.",
                body,
            ),
            Paragraph(
                "In patients with an eGFR between 30 and 45 mL/min/1.73m^2, Metformin dose "
                "should be reduced and renal function monitored every 3-6 months.",
                body,
            ),
        ],
    ),
    (
        "Section 4. Second-line Therapy",
        h1,
        [
            Paragraph(
                "When Metformin is contraindicated or not tolerated, second-line therapy "
                "should be individualized based on comorbidities:",
                body,
            ),
            Paragraph(
                "(a) SGLT2 Inhibitors (e.g. Empagliflozin, Dapagliflozin) are recommended "
                "particularly for patients with established cardiovascular disease, heart "
                "failure, or chronic kidney disease, given demonstrated cardiorenal benefit.",
                body,
            ),
            Paragraph(
                "(b) GLP-1 Receptor Agonists (e.g. Liraglutide, Semaglutide) are recommended "
                "particularly for patients with established atherosclerotic cardiovascular "
                "disease or where weight reduction is a clinical priority.",
                body,
            ),
        ],
    ),
    (
        "Section 5. Target HbA1c and Monitoring",
        h1,
        [
            Paragraph(
                "Target HbA1c is generally below 7.0% (53 mmol/mol) for most non-pregnant "
                "adults. A less stringent target (e.g. &lt; 8.0%) may be appropriate for "
                "patients with limited life expectancy, extensive comorbidity, or a history "
                "of severe hypoglycemia.",
                body,
            ),
            Paragraph(
                "HbA1c should be reassessed every 3 months until stable at target, then at "
                "least every 6 months thereafter.",
                body,
            ),
        ],
    ),
    (
        "Section 5.1 Heart Failure Caution",
        h1,
        [
            Paragraph(
                "In patients with Type 2 Diabetes and concurrent Heart Failure, "
                "Thiazolidinediones (e.g. Pioglitazone) are contraindicated due to the risk "
                "of fluid retention and exacerbation of Heart Failure symptoms.",
                body,
            ),
            Paragraph(
                "SGLT2 Inhibitors are preferred in this population: large outcome trials have "
                "shown a reduction in Heart Failure hospitalization independent of glycemic "
                "benefit, and they are considered appropriate even in patients with reduced "
                "ejection fraction.",
                body,
            ),
        ],
    ),
    (
        "Section 6. Renal Impairment Considerations",
        h1,
        [
            Paragraph(
                "SGLT2 Inhibitors may be initiated down to an eGFR of 20 mL/min/1.73m^2 for "
                "patients with established chronic kidney disease, given their renal-protective "
                "effect, but glycemic efficacy diminishes at lower eGFR.",
                body,
            ),
            Paragraph(
                "GLP-1 Receptor Agonists generally require no dose adjustment based on renal "
                "function and may be preferred when SGLT2 Inhibitors are not tolerated in "
                "patients with advanced chronic kidney disease.",
                body,
            ),
        ],
    ),
]


def build():
    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title="Qatar Diabetes Guideline 2023 (Simulated)",
    )
    story = []
    for i, (heading, style, paragraphs) in enumerate(PAGES):
        story.append(Paragraph(heading, style))
        story.extend(paragraphs)
        if i < len(PAGES) - 1:
            story.append(PageBreak())
    doc.build(story)
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
