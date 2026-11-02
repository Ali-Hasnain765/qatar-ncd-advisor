import hashlib
import json
import time
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types
import toml

import rag

# ==========================
# UI Configuration
# ==========================
st.set_page_config(page_title="Qatar NCD Advisor", layout="wide")

# ==========================
# SECURE API CONNECTION
# ==========================
try:
    secrets = toml.load("secrets.toml")
    api_key = secrets["general"]["GOOGLE_API_KEY"]
except FileNotFoundError:
    st.error("secrets.toml not found.")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-3.1-flash-lite"

# ==========================
# Guidelines
# "diabetes" ships with a bundled, simulated multi-page PDF (not an official MoPH
# document - created for this portfolio project) that is chunked, embedded, and
# indexed for real retrieval. A physician can upload their own PDF to replace it.
# ==========================
GUIDELINES = {
    "diabetes": {
        "available": True,
        "default_pdf": "guidelines/qatar_diabetes_guideline_2023_simulated.pdf",
        "display_name": {
            "en": "Qatar Diabetes Guideline 2023 (Simulated)",
            "ar": "دليل قطر لإدارة مرض السكري 2023 (محاكى)",
        },
    },
    "hypertension": {
        "available": False,
        "default_pdf": None,
        "display_name": {
            "en": "Qatar Hypertension Guideline 2023",
            "ar": "دليل قطر لارتفاع ضغط الدم 2023",
        },
    },
}

PROFILE_PROMPT_TEXT = {
    "new": "New Patient (first visit for this condition)",
    "existing_stable": "Existing Patient - Stable (established, well-controlled)",
    "existing_complex": "Existing Patient - Complex (multiple comorbidities / uncontrolled)",
}

# Synthetic, clearly-labeled demo patients used to auto-fill the notes field when a
# physician picks "Existing - Stable" or "Existing - Complex". Nothing here is real
# patient data, and none of it is ever written to disk - it only exists so a demo
# of the "existing patient" flow doesn't require an actual patient database, which
# would conflict with the project's "nothing is persisted" privacy stance.
DEMO_PATIENTS = {
    "new": {
        "en": (
            "55-year-old male. Newly diagnosed Type 2 Diabetes. BMI 34. HbA1c 8.5%. "
            "History of stable heart failure. Contraindicated for Metformin due to GI intolerance. "
            "Provide recommendation for first-line therapy."
        ),
        "ar": (
            "ذكر يبلغ من العمر 55 عامًا. تشخيص حديث بداء السكري من النوع الثاني. مؤشر كتلة الجسم 34. "
            "HbA1c 8.5%. تاريخ من قصور القلب المستقر. يوجد تعارض مع الميتفورمين بسبب عدم تحمل الجهاز الهضمي. "
            "يرجى تقديم توصية للعلاج الأولي."
        ),
    },
    "existing_stable": {
        "en": (
            "Demo Patient #204 (synthetic, not a real record). 61-year-old female. Established "
            "Type 2 Diabetes, diagnosed 2016. Currently on Metformin 1000mg twice daily, well "
            "tolerated. Last HbA1c 6.8%. eGFR 88. No known cardiovascular or renal complications. "
            "Attending for routine 6-month follow-up; no new symptoms."
        ),
        "ar": (
            "مريضة تجريبية رقم 204 (بيانات افتراضية، ليست سجلًا حقيقيًا). أنثى تبلغ من العمر 61 عامًا. "
            "مصابة بداء السكري من النوع الثاني منذ عام 2016. تتناول حاليًا ميتفورمين 1000 ملغ مرتين "
            "يوميًا بتحمل جيد. آخر قياس HbA1c كان 6.8%. eGFR 88. لا توجد مضاعفات قلبية أو كلوية معروفة. "
            "تحضر لمتابعة روتينية كل 6 أشهر؛ دون أعراض جديدة."
        ),
    },
    "existing_complex": {
        "en": (
            "Demo Patient #318 (synthetic, not a real record). 68-year-old male. Type 2 Diabetes "
            "for 12 years, HbA1c 9.2%. Chronic Kidney Disease stage 3b, eGFR 32. History of Heart "
            "Failure with reduced ejection fraction, currently stable on guideline-directed heart "
            "failure therapy. Currently on Metformin 500mg daily; being considered for treatment "
            "intensification. No known Metformin intolerance."
        ),
        "ar": (
            "مريض تجريبي رقم 318 (بيانات افتراضية، ليست سجلًا حقيقيًا). ذكر يبلغ من العمر 68 عامًا. "
            "مصاب بداء السكري من النوع الثاني منذ 12 عامًا، HbA1c 9.2%. مرض كلوي مزمن المرحلة 3ب، "
            "eGFR 32. تاريخ من قصور القلب مع انخفاض الكسر القذفي، مستقر حاليًا على العلاج الموجه وفق "
            "الإرشادات. يتناول حاليًا ميتفورمين 500 ملغ يوميًا؛ يُنظر حاليًا في تكثيف العلاج. لا يوجد "
            "عدم تحمل معروف للميتفورمين."
        ),
    },
}

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "status": {
            "type": "STRING",
            "enum": ["ok", "insufficient_info", "conflict", "not_found"],
        },
        "recommendation": {"type": "STRING"},
        "rationale": {"type": "STRING"},
        "missing_fields": {"type": "ARRAY", "items": {"type": "STRING"}},
        "conflict_warning": {"type": "STRING"},
        "citation_source_id": {"type": "STRING"},
    },
    "required": [
        "status",
        "recommendation",
        "rationale",
        "missing_fields",
        "conflict_warning",
        "citation_source_id",
    ],
}


def build_system_instruction(lang):
    language_name = "Arabic" if lang == "ar" else "English"
    return f"""You are a Clinical Decision Support Assistant for Qatar Ministry of
Public Health (MoPH) Primary Health Care physicians. Reason ONLY from the GUIDELINE
PASSAGES given below, which were retrieved from an uploaded PDF. Never use outside
medical knowledge and never invent a citation.

Each passage is tagged with a source id like [R2] and its real PDF page number. When
your recommendation relies on a passage, set citation_source_id to that single tag
(e.g. "R2").

Choose exactly one "status":
- "ok": the notes contain enough information (diagnosis/presentation plus relevant
  labs such as HbA1c or eGFR, plus current medications or contraindications) to give
  a guideline-concordant recommendation safely.
- "insufficient_info": the notes are too vague to safely recommend anything (e.g. no
  vitals, no history). List the specific missing_fields the physician must supply.
- "conflict": the guideline's usual recommendation needs special caution because of
  another condition mentioned in the notes (e.g. a therapy generally preferred for
  T2DM that the retrieved passages flag as risky with Heart Failure, renal
  impairment, etc). Explain the conflict in conflict_warning and still give your best
  cautious recommendation, including a note to consult the relevant specialist.
- "not_found": the question is outside the retrieved passages entirely (e.g. asks
  about a drug or condition never mentioned in them). Do not guess.

Respond in {language_name} for recommendation, rationale, conflict_warning, and
missing_fields. The "status" field must always be exactly one of these literal
English tokens: ok, insufficient_info, conflict, not_found - never translate it.
recommendation and rationale must be concise and clinician-facing. Leave
missing_fields and conflict_warning empty unless their matching status applies.
"""


LANG_STRINGS = {
    "en": {
        "app_title": "Qatar NCD Advisor | Ministry of Public Health",
        "clinical_context": "Clinical Context",
        "select_guideline": "Select Guideline",
        "select_profile": "Select Patient Profile",
        "helper_text": "Selected MoPH protocol establishes the boundaries for AI responses.",
        "patient_notes_header": "Patient Presentation Notes",
        "clinical_notes_label": "Clinical Notes",
        "placeholder": (
            "Enter relevant clinical details, vitals, and co-morbidities... "
            "(e.g., 55M, T2DM diagnosed 2018, HbA1c 8.5%, on Metformin 1g daily, eGFR 60)"
        ),
        "button": "Get Guideline Recommendation",
        "advisor_output": "Advisor Output",
        "empty_state": "Enter patient notes and click 'Get Guideline Recommendation' to view guideline-concordant advice here.",
        "recommendation_generated": "Recommendation Generated",
        "recommended_action": "Recommended Action",
        "source_reference": "Source Reference",
        "system_limitation": "System Limitation",
        "insufficient_prefix": "Information not sufficient to form a recommendation based only on the provided Qatar guidelines. Please include:",
        "not_found": "Information not found in the provided Qatar MoPH Guidelines.",
        "conflict_identified": "Guideline Conflict Identified",
        "recommended_action_caution": "Recommended Action (With Caution)",
        "conflict_label": "Conflict:",
        "consult_specialist": "Recommendation: Consult the relevant specialist before initiating therapy.",
        "disclaimer": "AI provides recommendations, not diagnoses. Physician discretion is required. Prototype V1.2.",
        "upload_pdf_label": "Upload Guideline PDF (optional)",
        "upload_pdf_help": "Replaces the bundled simulated guideline with your own PDF. Indexed in memory for this session only.",
        "indexed_caption": "Indexed {chunks} passages from {pages} pages.",
        "hypertension_warning": "{label} is not loaded in this prototype yet. Only Diabetes Management 2023 has an active knowledge base.",
        "prototype_badge": "Prototype V1.2 (Real PDF RAG + bilingual)",
        "language_label": "Language",
        "profile_new": "New Patient",
        "profile_existing_stable": "Existing - Stable",
        "profile_existing_complex": "Existing - Complex",
        "guideline_diabetes_label": "Diabetes Management 2023 (Active)",
        "guideline_hypertension_label": "Hypertension 2023",
        "please_valid_notes": "Please enter valid patient notes.",
        "indexing_spinner": "Indexing guideline PDF...",
        "consulting_spinner": "Consulting Qatar MoPH Guidelines...",
        "rag_error_prefix": "Could not index the guideline PDF:",
        "demo_patient_notice": "Synthetic demo patient for this prototype - not a real record, and nothing here is stored.",
    },
    "ar": {
        "app_title": "مستشار الأمراض غير السارية في قطر | وزارة الصحة العامة",
        "clinical_context": "السياق السريري",
        "select_guideline": "اختر البروتوكول الإرشادي",
        "select_profile": "اختر نوع المريض",
        "helper_text": "يحدد البروتوكول المختار من وزارة الصحة العامة حدود استجابات الذكاء الاصطناعي.",
        "patient_notes_header": "ملاحظات حالة المريض",
        "clinical_notes_label": "الملاحظات السريرية",
        "placeholder": (
            "أدخل التفاصيل السريرية ذات الصلة والعلامات الحيوية والأمراض المصاحبة... "
            "(مثال: ذكر 55 عامًا، سكري نوع 2 منذ 2018، HbA1c 8.5%، ميتفورمين 1غم يوميًا، eGFR 60)"
        ),
        "button": "احصل على التوصية الإرشادية",
        "advisor_output": "مخرجات المستشار",
        "empty_state": "أدخل ملاحظات المريض واضغط على 'احصل على التوصية الإرشادية' لعرض التوصية المتوافقة مع الإرشادات هنا.",
        "recommendation_generated": "تم إنشاء التوصية",
        "recommended_action": "الإجراء الموصى به",
        "source_reference": "المرجع المصدر",
        "system_limitation": "قيود النظام",
        "insufficient_prefix": "المعلومات غير كافية لتكوين توصية بناءً على الإرشادات القطرية المتوفرة فقط. يرجى تضمين:",
        "not_found": "لم يتم العثور على هذه المعلومات ضمن إرشادات وزارة الصحة العامة القطرية المتوفرة.",
        "conflict_identified": "تم تحديد تعارض في الإرشادات",
        "recommended_action_caution": "الإجراء الموصى به (مع التحذير)",
        "conflict_label": "التعارض:",
        "consult_specialist": "التوصية: يرجى استشارة الطبيب الاختصاصي المعني قبل بدء العلاج.",
        "disclaimer": "يقدم الذكاء الاصطناعي توصيات وليس تشخيصًا. يتطلب الأمر تقدير الطبيب المعالج. نسخة تجريبية V1.2.",
        "upload_pdf_label": "تحميل ملف PDF للإرشادات (اختياري)",
        "upload_pdf_help": "يستبدل الإرشاد المدمج المحاكى بملف PDF الخاص بك. تتم الفهرسة في الذاكرة لهذه الجلسة فقط.",
        "indexed_caption": "تمت فهرسة {chunks} مقطعًا من {pages} صفحة.",
        "hypertension_warning": "{label} غير محمّل في هذا النموذج التجريبي بعد. فقط إدارة السكري 2023 تحتوي على قاعدة معرفية فعالة.",
        "prototype_badge": "نسخة تجريبية V1.2 (RAG حقيقي لملفات PDF + دعم ثنائي اللغة)",
        "language_label": "اللغة",
        "profile_new": "مريض جديد",
        "profile_existing_stable": "مريض سابق - مستقر",
        "profile_existing_complex": "مريض سابق - حالة معقدة",
        "guideline_diabetes_label": "إدارة مرض السكري 2023 (نشط)",
        "guideline_hypertension_label": "ارتفاع ضغط الدم 2023",
        "please_valid_notes": "يرجى إدخال ملاحظات صحيحة عن المريض.",
        "indexing_spinner": "جارٍ فهرسة ملف الإرشادات...",
        "consulting_spinner": "جارٍ الرجوع إلى إرشادات وزارة الصحة العامة القطرية...",
        "rag_error_prefix": "تعذرت فهرسة ملف PDF الخاص بالإرشادات:",
        "demo_patient_notice": "مريض تجريبي افتراضي لهذا النموذج الأولي - ليس سجلًا حقيقيًا، ولا يتم تخزين أي شيء هنا.",
    },
}

# ==========================
# Session State
# ==========================
st.session_state.setdefault("lang", "en")
st.session_state.setdefault("last_result", None)
st.session_state.setdefault("last_error", None)
st.session_state.setdefault("rag_cache_key", None)
st.session_state.setdefault("rag_collection", None)
st.session_state.setdefault("rag_chunk_count", 0)
st.session_state.setdefault("rag_page_count", 0)
st.session_state.setdefault("prev_profile_key", "new")
st.session_state.setdefault("patient_notes", DEMO_PATIENTS["new"]["en"])

lang = st.session_state.lang
T = LANG_STRINGS[lang]
is_rtl = lang == "ar"

if is_rtl:
    st.markdown(
        "<style>.stApp, .stApp [data-testid='stMarkdownContainer'] { direction: rtl; text-align: right; }"
        ".stApp [data-testid='stSidebar'] { direction: rtl; text-align: right; }</style>",
        unsafe_allow_html=True,
    )

# ==========================
# RAG indexing (cached per uploaded-or-default PDF)
# ==========================


def generate_with_retry(**kwargs):
    """Gemini's hosted models occasionally return a transient 503 under high demand.
    Retry a few times with backoff before surfacing an error to the physician."""
    last_error = None
    for attempt, delay in enumerate([0, 3]):
        if delay:
            time.sleep(delay)
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            last_error = e
            if "503" not in str(e) and "UNAVAILABLE" not in str(e):
                raise
    raise last_error


def get_or_build_index(pdf_bytes, guideline_key):
    cache_key = f"{guideline_key}:{hashlib.md5(pdf_bytes).hexdigest()}"
    if st.session_state.rag_cache_key != cache_key:
        with st.spinner(T["indexing_spinner"]):
            chunks = rag.extract_pdf_chunks(pdf_bytes, source_id=guideline_key)
            collection = rag.build_index(client, chunks, collection_name=cache_key.replace(":", "_")[:60])
        st.session_state.rag_cache_key = cache_key
        st.session_state.rag_collection = collection
        st.session_state.rag_chunk_count = len(chunks)
        st.session_state.rag_page_count = len({c["page"] for c in chunks})
    return st.session_state.rag_collection


# ==========================
# Header
# The logo stays visually on the left in both languages, per the Design Spec's
# bilingual note ("The MoPH Logo remains on the left (standard)") - the RTL flip
# otherwise reverses flex child order, so the DOM order below is swapped for Arabic.
# ==========================
if is_rtl:
    col_title, col_logo = st.columns([9, 1])
else:
    col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.image("assets/ncd_advisor_logo.png", width=64)
with col_title:
    st.title(T["app_title"])
st.markdown("---")

# ==========================
# Column 1: Clinical Context (sidebar)
# ==========================
with st.sidebar:
    lang_choice = st.selectbox(
        T["language_label"], options=["en", "ar"], format_func=lambda k: "English" if k == "en" else "العربية",
        index=0 if lang == "en" else 1,
        key="lang_select",
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        if st.session_state.prev_profile_key in DEMO_PATIENTS:
            st.session_state.patient_notes = DEMO_PATIENTS[st.session_state.prev_profile_key][lang_choice]
        st.rerun()

    st.header(T["clinical_context"])

    # A selectbox whose format_func output changes language can desync its stored
    # selection from a valid option on BaseWeb Select's re-mount (it can't match
    # the old selection against the newly-translated labels). Keying each widget
    # per language sidesteps that: switching language mounts a fresh widget
    # instance, which we pre-seed below from our own canonical tracked value, so
    # the visible selection survives a language toggle instead of desyncing.
    st.session_state.setdefault("guideline_key_canonical", "diabetes")
    guideline_widget_key = f"guideline_select_{lang}"
    if st.session_state.get(guideline_widget_key) not in GUIDELINES:
        st.session_state[guideline_widget_key] = st.session_state.guideline_key_canonical

    guideline_key = st.selectbox(
        T["select_guideline"],
        options=list(GUIDELINES.keys()),
        format_func=lambda k: T["guideline_diabetes_label"] if k == "diabetes" else T["guideline_hypertension_label"],
        key=guideline_widget_key,
    )
    st.session_state.guideline_key_canonical = guideline_key
    guideline = GUIDELINES[guideline_key]

    profile_widget_key = f"profile_select_{lang}"
    if st.session_state.get(profile_widget_key) not in DEMO_PATIENTS:
        st.session_state[profile_widget_key] = st.session_state.prev_profile_key

    profile_key = st.selectbox(
        T["select_profile"],
        options=["new", "existing_stable", "existing_complex"],
        format_func=lambda k: {
            "new": T["profile_new"],
            "existing_stable": T["profile_existing_stable"],
            "existing_complex": T["profile_existing_complex"],
        }[k],
        key=profile_widget_key,
    )
    if profile_key != st.session_state.prev_profile_key:
        st.session_state.patient_notes = DEMO_PATIENTS[profile_key][lang]
        st.session_state.prev_profile_key = profile_key

    st.caption(T["helper_text"])

    rag_error = None
    uploaded_pdf = None
    if guideline["available"]:
        uploaded_pdf = st.file_uploader(
            T["upload_pdf_label"], type="pdf", help=T["upload_pdf_help"], key="pdf_uploader"
        )
        pdf_bytes = uploaded_pdf.read() if uploaded_pdf else Path(guideline["default_pdf"]).read_bytes()
        try:
            get_or_build_index(pdf_bytes, guideline_key)
            st.caption(
                T["indexed_caption"].format(
                    chunks=st.session_state.rag_chunk_count, pages=st.session_state.rag_page_count
                )
            )
        except Exception as e:
            rag_error = str(e)
            st.error(f"{T['rag_error_prefix']} {rag_error}")
    else:
        st.warning(T["hypertension_warning"].format(label=T["guideline_hypertension_label"]))

    st.info(T["prototype_badge"])

# ==========================
# Column 2: Patient Presentation Notes / Column 3: Advisor Output
# ==========================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(T["patient_notes_header"])
    if profile_key in ("existing_stable", "existing_complex"):
        st.caption(f"🧪 {T['demo_patient_notice']}")
    patient_notes = st.text_area(
        T["clinical_notes_label"],
        height=200,
        key="patient_notes",
        max_chars=2000,
        placeholder=T["placeholder"],
    )
    st.caption(f"{len(patient_notes)}/2000")

    get_recommendation = st.button(
        T["button"],
        type="primary",
        disabled=not guideline["available"] or rag_error is not None,
    )

with col2:
    st.subheader(T["advisor_output"])

    if get_recommendation:
        if not patient_notes or len(patient_notes.strip()) < 10:
            st.session_state.last_result = None
            st.session_state.last_error = None
            st.warning(T["please_valid_notes"])
        else:
            with st.spinner(T["consulting_spinner"]):
                collection = st.session_state.rag_collection
                retrieved = rag.retrieve(client, collection, query=patient_notes, k=5)

                tag_lookup = {}
                tagged_parts = []
                for i, chunk in enumerate(retrieved, start=1):
                    tag = f"R{i}"
                    tag_lookup[tag] = chunk
                    tagged_parts.append(f"[{tag}] (Page {chunk['page']}): {chunk['text']}")
                guideline_text = "\n\n".join(tagged_parts)

                complexity_note = (
                    "This is flagged as an Existing - Complex patient: scrutinize the notes "
                    "closely for multi-morbidity conflicts before answering.\n"
                    if profile_key == "existing_complex"
                    else ""
                )

                full_prompt = (
                    f"{build_system_instruction(lang)}\n\n"
                    f"GUIDELINE PASSAGES ({guideline['display_name'][lang]}):\n{guideline_text}\n\n"
                    f"PATIENT PROFILE: {PROFILE_PROMPT_TEXT[profile_key]}\n"
                    f"{complexity_note}"
                    f"PATIENT PRESENTATION NOTES:\n{patient_notes}"
                )

                try:
                    response = generate_with_retry(
                        model=MODEL_NAME,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            top_p=0.9,
                            top_k=40,
                            response_mime_type="application/json",
                            response_schema=RESPONSE_SCHEMA,
                            safety_settings=[
                                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                            ],
                        ),
                    )
                    data = json.loads(response.text)

                    source = tag_lookup.get(data.get("citation_source_id", ""))
                    data["_citation_display"] = (
                        f"{guideline['display_name'][lang]}, Page {source['page']}"
                        if source
                        else None
                    )

                    st.session_state.last_result = data
                    st.session_state.last_error = None
                except Exception as e:
                    st.session_state.last_result = None
                    st.session_state.last_error = str(e)

    result = st.session_state.last_result
    error = st.session_state.last_error

    if error:
        st.error(f"Generation Error: {error}")
        st.code(error)

    elif result is None:
        st.markdown(
            "<div style='text-align:center; padding-top:48px; opacity:0.5;'>"
            "<div style='font-size:48px;'>&#128196;</div>"
            f"<p>{T['empty_state']}</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    elif result["status"] == "ok":
        st.success(T["recommendation_generated"])
        st.markdown(f"#### {T['recommended_action']}")
        st.write(result["recommendation"])
        if result.get("rationale"):
            st.caption(result["rationale"])
        with st.container(border=True):
            st.markdown(f"**{T['source_reference']}**")
            st.write(result.get("_citation_display") or guideline["display_name"][lang])

    elif result["status"] == "conflict":
        st.warning(T["conflict_identified"])
        st.markdown(f"#### {T['recommended_action_caution']}")
        st.write(result["recommendation"])
        if result.get("conflict_warning"):
            st.markdown(f"**{T['conflict_label']}** {result['conflict_warning']}")
        if result.get("rationale"):
            st.caption(result["rationale"])
        with st.container(border=True):
            st.markdown(f"**{T['source_reference']}**")
            st.write(result.get("_citation_display") or guideline["display_name"][lang])
        st.info(T["consult_specialist"])

    elif result["status"] in ("insufficient_info", "not_found"):
        st.markdown(
            "<div style='border-left:4px solid #FFC107; padding:10px 14px; "
            "background:rgba(255,193,7,0.10); margin-bottom:10px;'>"
            f"<strong style='color:#FFC107;'>{T['system_limitation']}</strong></div>",
            unsafe_allow_html=True,
        )
        if result["status"] == "insufficient_info":
            missing = ", ".join(result.get("missing_fields", [])) or "-"
            st.write(f"{T['insufficient_prefix']} {missing}.")
        else:
            st.write(T["not_found"])

st.markdown("---")
st.caption(T["disclaimer"])
