Project Definition Document: Qatar NCD Advisor
1. Executive Summary & Problem Statement
The Context: Qatar faces a high prevalence of Non-Communicable Diseases (NCDs), specifically Type 2 Diabetes and Hypertension. Primary Health Care (PHC) physicians operate under severe time constraints (10-15 minutes per patient).
The Problem: Clinical guidelines for managing these diseases are complex, voluminous (often 100+ pages), and updated frequently. Expecting physicians to memorize these updates or consult lengthy documents during a consultation is inefficient and increases the risk of variability in care.
The Solution: A secure, localized Clinical Decision Support System (CDSS) utilizing Retrieval-Augmented Generation (RAG) to provide instant, guideline-concordant answers to physician queries based only on trusted Qatar Ministry of Public Health (MoPH) protocols.
2. Target User & Personas
Primary User: General Practitioner or Family Physician at a Primary Health Care Corporation (PHCC) center in Qatar.
Persona Example:
Name: Dr. Fatima
Experience: 7 years
Pain Point: "I see 35 patients a day. A patient just presented with uncontrolled diabetes and early-stage chronic kidney disease. I need to know the exact preferred second-line therapy according to current Qatar guidelines, but I don't have time to search through a PDF."
3. Scope & MVP (Minimum Viable Product)
To demonstrate competence without over-scoping, the MVP will focus on:
Disease Area: Type 2 Diabetes Mellitus (T2DM) Management (Adults).
Data Source: A single, authoritative PDF guideline document (simulated or publicly sourced MoPH document).
Platform: Web application (Streamlit interface).
Core Functionality: Query-response system with source citation.
4. User Journey (Happy Path vs. Edge Cases)
Scenario A: The Happy Path (Standard Query)
Input: Dr. Fatima logs in securely. She selects "T2DM Guidelines." She types: "Newly diagnosed T2DM patient, BMI 35, HbA1c 8.5%. Contraindicated for Metformin due to GI issues. What is first-line monotherapy?"
Processing: The system retrieves relevant paragraphs from the uploaded PDF. Gemini synthesizes an answer based only on that text.
Output: The app displays: "Based on Qatar T2DM Guidelines (Page 42), as Metformin is contraindicated, consider initiating GLP-1 Receptor Agonist or SGLT2 Inhibitor, bearing in mind cardiovascular risk factors." It provides a link/reference to Page 42.
Outcome: Dr. Fatima verifies the source, makes a quick clinical decision, and proceeds. Total time: 30 seconds.
Scenario B: The Neutral Path (Insufficient Information)
Input: Dr. Fatima types: "Treat patient X."
Processing: Gemini cannot form a clinical recommendation due to lack of specifics (no vitals, no history).
Output: "Information insufficient to provide a recommendation. Please specify patient age, HbA1c, comorbidities, and current medications."
Scenario C: The Edge Case (Multi-morbidity/Conflict)
Input: Patient has T2DM and severe Heart Failure. Guidelines for T2DM suggest drug A, but guidelines for Heart Failure suggest drug A might be harmful.
Processing: The prompt instructs Gemini to identify conflicts.
Output: "Identified conflict: Guideline indicates Drug A for T2DM, but patient history of Heart Failure requires caution with Drug A (Source: Section 5.1). Recommendation: Consult Endocrinology specialist before initiating."
Scenario D: The Failure Path (Hallucination Attempt)
Input: Dr. Fatima asks about a drug not approved in Qatar yet (e.g., a very new experimental drug).
Processing: Gemini searches the PDF. It is not there.
Output (Guarded): "Information not found in the provided Qatar MoPH Guidelines." (The system strictly refuses to use external knowledge).
5. Information Architecture (Sitemap)
The system is a Single Page Application (SPA) designed for speed.
Landing Page (Authentication)
Secure Login (simulated for portfolio).
Main Dashboard (The Clinician View)
[Header] - User Profile, Institution (HMC/PHCC).
[Sidebar] - Guideline Selector (Dropdown: Diabetes, Hypertension).
[Main Area] - Input Section (Text area for patient details).
[Main Area] - Action Button ("Get Recommendation").
[Main Area] - Output Section (Text box for AI response + Citation link).
6. Technical Requirements & Security (The "How")
Since you are not a coder, these are the specifications we will follow to build it using AI assistance.
Frontend: Streamlit (Python library).
Backend Logic: Python.
AI/LLM: Google Gemini Pro 1.5 Flash (via API). Selected for speed and high context window.
AI Infrastructure: Google AI Studio (used to upload the PDF and create the "tuned/grounded" model instance).
Security & Privacy (Crucial for HBKU):
Data in Transit: Encrypted via HTTPS.
Data at Rest: Patient data entered by the doctor is NOT stored in a database. It is sent via API, processed ephemerally (in memory) by Gemini, and discarded immediately.
Compliance Acknowledgment: The portfolio must state that the prototype is designed with principles aligned with Qatar's National Health Information Security standards (though full certification is outside the scope of a student project).
7. Testing & Validation Strategy (Interview Prep)
How will you prove it works?
Unit Testing: Verify the UI elements load.
Grounding/Retrieval Testing: Create a "Gold Standard" dataset of 15 patient scenarios. Compare the app's output against the manual lookup in the PDF.
Metric: Target 100% adherence to the guideline text (no hallucinations).
User Acceptance Testing (UAT) - Simulated: Walk a medically trained friend through the app to see if the workflow makes sense to a non-tech user.



Design Specification: Qatar NCD Advisor
1. Design Principles & Constraints
Context: Clinical setting. High cognitive load, potential time poverty for users.
Device: Desktop-first (Clinicians use workstations).
Aesthetics: "Sterile Trust." Clean, minimal, high contrast. Based on HMC/PHCC branding (Greys, Whites, subtle Teals for action).
Accessibility: WCAG AA compliant (Contrast ratio 
≥
≥
 4.5:1 for body text).
Density: Information-dense but not cluttered. Utilize an 8pt grid.
2. Interaction Model: AI-Native (Human-in-the-loop)
We must avoid the "black box" anti-pattern. The clinician is the ultimate decision-maker.
Input Transparency: The system clearly indicates which guideline is being used.
Processing State: Explicit loading state while Gemini retrieves and synthesizes data.
Output Validation: The AI response is presented not just as text, but with mandatory Source Citations (e.g., "Page 42, Section 3.2").
Override/Feedback: Implicitly, the doctor overrides the AI by choosing whether to act. (Future versions would include a Thumbs Up/Down explicitly).
3. Wireframe & Layout Strategy (Desktop)
We will use a 3-column layout to manage the workflow efficiently.
Global Elements (Header)
Left: Logo (Qatar NCD Advisor - Ministry of Public Health branding).
Right: User Profile (Dr. Fatima Al-Khater), Logout.
Column 1: Context & Input (The "Setup")
Header: "Clinical Context"
Control 1 (Dropdown): Select Guideline. Options: [Diabetes Management 2023 (Active)], [Hypertension 2023].
Control 2 (Dropdown): Patient Profile. Options: [New Patient], [Existing - Stable], [Existing - Complex].
Helper Text: "Selected MoPH protocol establishes the boundaries for AI responses."
Column 2: The Query (The "Work")
Header: "Patient Presentation Notes"
Input Field: Large multi-line text area (Textarea).
Placeholder: "Enter relevant clinical details, vitals, and co-morbidities... (e.g., 55M, T2DM diagnosed 2018, HbA1c 8.5%, on Metformin 1g daily, eGFR 60)"
Character Counter: Visible but subtle (e.g., 0/2000).
Action Button: Primary CTA button (Teal background). Label: "Get Guideline Recommendation".
Column 3: The Advisor (The "Insight")
This column changes state based on the interaction.
State A: Empty State (Default)
Icon: Large, faint document icon.
Text: "Enter patient notes and click 'Get Recommendation' to view guideline-concordant advice here."
State B: Loading State
Component: Standard Streamlit spinner + text "Consulting Qatar MoPH Guidelines..."
State C: Result State (Success)
Header: "Recommended Action" (High contrast text).
Body: Markdown formatted text containing the synthesized advice.
Citation Box (Distinct UI block):
Header: "Source Reference"
Text: "Qatar Diabetes Guideline 2023, Page 42, Section 4.2: First-line Therapy."
Interaction: Hovering highlights the relevant text in the original PDF (simulated).
Disclaimer: Small, footer text: "AI provides recommendations, not diagnoses. Physician discretion is required."
State D: Error State (Edge Case)
Header: "System Limitation" (Amber text).
Body: "Information not sufficient to form a recommendation based only on the provided Qatar guidelines. Please include HbA1c and renal function."
4. Design System Tokens (Partial)
Color Palette:
Primary: Teal (#008080)
Background: White (#FFFFFF)
Surface: Off-White/Grey 50 (#F8F9FA)
Text: Dark Grey (#212529)
Borders: Grey 300 (#DEE2E6)
Accent (Errors): Amber (#FFC107)
Typography (IBM Plex Sans - chosen for readability and professional look):
H1 (Header): 24pt Bold
H2 (Column Titles): 18pt Semi-Bold
Body: 16pt Regular
Spacing (8pt Grid):
Padding between columns: 24pt
Margin within cards: 16pt
Radius: 4pt (Sharp but professional)
Elevation: Subtle shadow on Column 3 to distinguish it as the output.




Design Specification: Qatar NCD Advisor (Bilingual & Dual-Theme)
1. Localization Strategy (English & Arabic)
The application header will feature a simple toggle.
Default: English (Left-to-Right layout).
Toggled: Arabic (Right-to-Left layout).
The change affects all text labels, headers, dropdown options, and placeholder text.
2. Theme Strategy (Light & Dark)
The color palette is adapted for accessibility in both modes.
Color Tokens:
Token	Light Mode Value	Dark Mode Value	Use Case
Primary Teal	#008080	#00BFA5	Buttons, Active States
Background	#FFFFFF (White)	#111111 (Charcoal)	Main Body
Surface	#F8F9FA (Grey 50)	#1E1E1E (Grey 800)	Columns, Cards
Text Main	#212529 (Grey 900)	#E0E0E0 (Grey 200)	Body Text
Accent Amber	#FFC107	#FFD54F	System Warnings
3. Visual Assets Generation
I will generate 4 images to cover the matrix of states.


Asset A: Light Mode | English (Default State)
This is the baseline professional look.

Asset B: Dark Mode | English
This shifts the theme while keeping the English context.

Asset C: Dark Mode | Arabic (Right-to-Left)
This is the most complex state, requiring RTL layout mirroring and Arabic text translation.
Visual Translation Notes:
The MoPH Logo remains on the left (standard).
The User Profile moves to the far right.
The 3-Column layout is mirrored: Clinical Context is now on the Right, and Advisor Output is on the Left.
The Arabic text is generated by Gemini Pro, which is highly accurate for medical terminology in Arabic.