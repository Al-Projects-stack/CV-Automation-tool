import json
import re
import subprocess
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FORMATTERS_DIR = BASE_DIR / "formatters"
OUTPUTS_DIR = BASE_DIR / "outputs"
FORMAT_CV_JS = FORMATTERS_DIR / "format_cv.js"
FORMAT_CL_JS = FORMATTERS_DIR / "format_cover_letter.js"


def safe_filename(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text).strip().replace(" ", "_")


def generate_documents(tailored: dict, master_cv: dict) -> Path:
    OUTPUTS_DIR.mkdir(exist_ok=True)

    role = safe_filename(tailored.get("role_title", "Role"))
    company = safe_filename(tailored.get("company", "Company"))

    cv_filename = f"CV_{role}_{company}.docx"
    cl_filename = f"CoverLetter_{role}_{company}.docx"
    zip_filename = f"Application_{role}_{company}.zip"

    cv_out = OUTPUTS_DIR / cv_filename
    cl_out = OUTPUTS_DIR / cl_filename
    zip_out = OUTPUTS_DIR / zip_filename

    _generate_cv(tailored, master_cv, cv_out)
    _generate_cover_letter(tailored, master_cv, cl_out)

    with zipfile.ZipFile(zip_out, "w") as zf:
        zf.write(cv_out, cv_filename)
        zf.write(cl_out, cl_filename)

    # clean up individual docx files after zipping
    cv_out.unlink(missing_ok=True)
    cl_out.unlink(missing_ok=True)

    return zip_out


def _generate_cv(tailored: dict, master_cv: dict, out_path: Path):
    merged = dict(tailored)
    merged["personal"] = master_cv["personal"]
    merged["education"] = master_cv["education"]

    tmp_json = OUTPUTS_DIR / f"tmp_tailored_{uuid.uuid4().hex}.json"
    with open(tmp_json, "w") as f:
        json.dump(merged, f, indent=2)

    try:
        result = subprocess.run(
            ["node", str(FORMAT_CV_JS), str(tmp_json), str(out_path)],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"CV generation failed: {e.stderr}")
    finally:
        tmp_json.unlink(missing_ok=True)


def _generate_cover_letter(tailored: dict, master_cv: dict, out_path: Path):
    info = master_cv["personal"]

    cover_data = {
        "name": info["name"],
        "email": info["email"],
        "phone": info["phone"],
        "location": info["location"],
        "date": datetime.today().strftime("%d %B %Y"),
        "role_title": tailored.get("role_title", ""),
        "company": tailored.get("company", ""),
        "cover_letter": tailored.get("cover_letter", "")
    }

    tmp_json = OUTPUTS_DIR / f"tmp_cover_{uuid.uuid4().hex}.json"
    with open(tmp_json, "w") as f:
        json.dump(cover_data, f, indent=2)

    try:
        result = subprocess.run(
            ["node", str(FORMAT_CL_JS), str(tmp_json), str(out_path)],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Cover letter generation failed: {e.stderr}")
    finally:
        tmp_json.unlink(missing_ok=True)
