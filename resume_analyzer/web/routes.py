"""
Routes.

Uploaded files are read into memory and analysed there; nothing is written to
disk. The result goes into a short-lived store under an unguessable key, and
the browser is redirected to that key.
"""

from __future__ import annotations

import io
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import (Blueprint, abort, current_app, jsonify, redirect, render_template,
                   request, send_file, url_for)
from pydantic import ValidationError

from ..criteria import get_category, get_registry
from ..extraction.document import DocumentError
from ..generator import generate
from ..generator.draft import ResumeDraft
from ..pipeline import analyze
from ..semantic import model
from .presenter import present

bp = Blueprint("main", __name__)

SAMPLES = {
    "clean": ("ats/clean_pdf__Priya_Sharma_Resume_SDE.pdf", "A tidy single-column resume"),
    "two_column": ("ats/two_column_pdf__resume.pdf", "A two-column template that parsers mangle"),
    "messy": ("ats/messy_docx__Resume.docx", "A Word file with contact details in the page header"),
}
SAMPLE_JD = "ats/sde_job_description.txt"


def _store():
    return current_app.extensions["results"]


def _categories() -> List[Any]:
    return sorted(get_registry().values(), key=lambda c: c.label)


def _form_inputs(category_id: str, form) -> Dict[str, Any]:
    """Read the category's declared inputs out of the submitted form."""
    values: Dict[str, Any] = {}
    for spec in get_category(category_id).inputs:
        raw = (form.get(f"input__{spec.id}") or "").strip()
        if not raw:
            continue
        if spec.type == "bool":
            values[spec.id] = raw.lower() in ("1", "true", "on", "yes")
        elif spec.type == "number":
            try:
                values[spec.id] = float(raw)
            except ValueError:
                continue
        else:
            values[spec.id] = raw
    return values


def _run(data: bytes, filename: str, category_id: str, jd_text: str, sop_text: str,
         inputs: Dict[str, Any]) -> str:
    result = analyze(data, filename, category_id, jd_text=jd_text or None,
                     inputs=inputs or None, sop_text=sop_text or None)
    return _store().put(result)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

@bp.get("/")
def home():
    return render_template("index.html", categories=_categories(), samples=SAMPLES,
                           model_ready=model.available())


@bp.post("/analyze")
def analyse():
    upload = request.files.get("resume")
    category_id = request.form.get("category", "tech_product_fulltime")
    if category_id not in get_registry():
        abort(400, "Unknown category")
    if not upload or not upload.filename:
        return render_template("error.html", title="No file chosen",
                               message="Choose a PDF, DOCX or TXT file to analyse."), 400
    try:
        key = _run(upload.read(), upload.filename, category_id,
                   request.form.get("jd", "").strip(), request.form.get("sop", "").strip(),
                   _form_inputs(category_id, request.form))
    except DocumentError as exc:
        return render_template("error.html", title="That file could not be read", message=str(exc)), 400
    except ValueError as exc:
        return render_template("error.html", title="Check the form", message=str(exc)), 400
    return redirect(url_for("main.result", key=key))


@bp.get("/sample/<name>")
def sample(name: str):
    if name not in SAMPLES:
        abort(404)
    path = Path(current_app.config["SAMPLES_DIR"]) / SAMPLES[name][0]
    jd_path = Path(current_app.config["SAMPLES_DIR"]) / SAMPLE_JD
    key = _run(path.read_bytes(), path.name.split("__")[-1], "tech_product_fulltime",
               jd_path.read_text(encoding="utf-8"), "", {})
    return redirect(url_for("main.result", key=key))


@bp.get("/r/<key>")
def result(key: str):
    analysis = _store().get(key)
    if analysis is None:
        return render_template("error.html", title="That result has expired",
                               message="Results are kept for a short time and then deleted. "
                                       "Upload the resume again to see a fresh report."), 404
    return render_template("result.html", **present(analysis, key, _store().expires_in(key)))


@bp.post("/r/<key>/delete")
def delete_result(key: str):
    _store().delete(key)
    return redirect(url_for("main.home", deleted=1))


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------

@bp.get("/build")
def build_form():
    category_id = request.args.get("category", "tech_product_fulltime")
    if category_id not in get_registry():
        abort(404)
    category = get_category(category_id)
    order = [s for s in (category.generator.section_order if category.generator else []) if s != "header"]
    return render_template("build.html", categories=_categories(), category=category, emphasis=order)


@bp.post("/build")
def build_submit():
    category_id = request.form.get("category", "tech_product_fulltime")
    if category_id not in get_registry():
        abort(400, "Unknown category")
    try:
        draft = ResumeDraft.from_payload(_draft_payload(request.form))
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"])
        return render_template("error.html", title="Check the form",
                               message=f"{field}: {first['msg']}"), 400
    generated = generate(draft, category_id, "pdf")
    key = _store().put({"draft": draft, "category": category_id})
    return render_template("build_done.html", key=key, generated=generated,
                           category=get_category(category_id))


@bp.get("/build/<key>/download/<file_format>")
def build_download(key: str, file_format: str):
    payload = _store().get(key)
    if not payload or "draft" not in payload:
        return render_template("error.html", title="That draft has expired",
                               message="Drafts are kept for a short time. Fill the form again."), 404
    try:
        generated = generate(payload["draft"], payload["category"], file_format)
    except ValueError as exc:
        abort(400, str(exc))
    mimetypes = {"pdf": "application/pdf",
                 "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    return send_file(io.BytesIO(generated.content), mimetype=mimetypes[file_format],
                     as_attachment=True, download_name=generated.filename)


def _rows(form, prefix: str, fields: List[str]) -> List[Dict[str, Any]]:
    """Collect repeated form rows named prefix__0__field, prefix__1__field, ..."""
    rows: Dict[int, Dict[str, Any]] = {}
    for key in form.keys():
        parts = key.split("__")
        if len(parts) != 3 or parts[0] != prefix or parts[2] not in fields:
            continue
        index = int(parts[1]) if parts[1].isdigit() else 0
        value = form.get(key, "").strip()
        row = rows.setdefault(index, {})
        if parts[2] == "bullets":
            row["bullets"] = [b.strip() for b in value.splitlines() if b.strip()]
        elif parts[2] == "items":
            row["items"] = [b.strip() for b in value.replace("\n", ",").split(",") if b.strip()]
        else:
            row[parts[2]] = value
    return [rows[i] for i in sorted(rows)]


def _lines(form, field: str) -> List[str]:
    return [line.strip() for line in (form.get(field) or "").splitlines() if line.strip()]


def _draft_payload(form) -> Dict[str, Any]:
    role_fields = ["title", "organisation", "location", "start", "end", "bullets"]
    return {
        "contact": {k: (form.get(f"contact__{k}") or "").strip()
                    for k in ("name", "email", "phone", "location", "linkedin", "github", "portfolio")},
        "summary": (form.get("summary") or "").strip(),
        "education": _rows(form, "education", ["qualification", "institution", "start", "end", "score"]),
        "experience": _rows(form, "experience", role_fields),
        "internships": _rows(form, "internships", role_fields),
        "research": _rows(form, "research", role_fields),
        "projects": _rows(form, "projects", ["title", "stack", "start", "end", "link", "bullets"]),
        "skills": _rows(form, "skills", ["label", "items"]),
        "coding_profiles": _lines(form, "coding_profiles"),
        "exams": _lines(form, "exams"),
        "publications": _lines(form, "publications"),
        "achievements": _lines(form, "achievements"),
        "certifications": _lines(form, "certifications"),
        "activities": _lines(form, "activities"),
        "coursework": [c.strip() for c in (form.get("coursework") or "").replace("\n", ",").split(",") if c.strip()],
        "languages": [c.strip() for c in (form.get("languages") or "").replace("\n", ",").split(",") if c.strip()],
        "date_of_birth": (form.get("date_of_birth") or "").strip(),
    }


# --------------------------------------------------------------------------
# JSON API
# --------------------------------------------------------------------------

@bp.get("/api/categories")
def api_categories():
    return jsonify([{"id": c.id, "label": c.label, "score_label": c.score_label, "examples": c.examples,
                     "inputs": [i.model_dump() for i in c.inputs]} for c in _categories()])


@bp.post("/api/analyze")
def api_analyze():
    upload = request.files.get("resume")
    if not upload or not upload.filename:
        return jsonify({"error": "attach a resume file as 'resume'"}), 400
    category_id = request.form.get("category", "tech_product_fulltime")
    if category_id not in get_registry():
        return jsonify({"error": f"unknown category '{category_id}'"}), 400
    try:
        result = analyze(upload.read(), upload.filename, category_id,
                         jd_text=request.form.get("jd") or None,
                         inputs=_form_inputs(category_id, request.form) or None,
                         sop_text=request.form.get("sop") or None)
    except DocumentError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "category": result.category.id,
        "name": result.name,
        "scores": result.scores,
        "confidence": result.strength.confidence,
        "eligible": result.strength.eligible,
        "strength": result.strength.to_dict(),
        "ats": {"score": result.ats.score, "fatal": result.ats.fatal,
                "groups": [{"id": g.id, "label": g.label, "score": g.score,
                            "checks": [{"id": c.id, "status": c.status, "message": c.message, "fix": c.fix}
                                       for c in g.checks]} for g in result.ats.groups],
                "fixes": [asdict(f) for f in result.ats.fixes]},
        "jd_fit": None if not result.jd_fit else {
            "score": result.jd_fit.score, "note": result.jd_fit.note,
            "matches": [asdict(m) for m in result.jd_fit.matches]},
        "features": result.extraction.features,
        "evidence": result.extraction.evidence,
        "timings_ms": result.timings_ms,
    })


@bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "semantic_model": model.available(),
                    "categories": len(get_registry()), "cached_results": len(_store())})
