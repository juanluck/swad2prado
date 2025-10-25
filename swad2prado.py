#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SWAD → PRADO (Moodle XML) converter (CLI)

- Usa CDATA con HTML (<p>…</p>) para los enunciados.
- La categoría SIEMPRE se pasa por "--category".
- **--mapping es opcional**: hay un mapping por defecto integrado.
- Sin dependencias externas (stdlib).

Ejemplos
--------
# Con mapping integrado (por defecto)
swad2prado examples/swad.xml examples/output/prado_out.xml \
  --category "$course$/top/Banco importado desde SWAD" \
  --shuffle true

# Sobrescribir mapping con un JSON externo
swad2prado examples/swad.xml examples/output/prado_out.xml \
  --mapping mapping.json \
  --category "$course$/top/Tema 1" \
  --shuffle false
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# ---- Mapping por defecto integrado ----------------------------------------
DEFAULT_MAPPING: Dict[str, Any] = {
    "question_xpath": ".//question",
    "title": "stem",
    "text": "stem",
    "text_format": "html",
    "answer_list": "answer/option",
    "answer_text": "text",
    "answer_is_correct": "@correct",
    "true_values": ["Yes", "yes", "1", "true", "si", "sí"],
    "feedback": None,
    "question_feedback": None,
}

TRUE_FALSE_ALIASES = {
    "true": {"true", "verdadero", "cierto", "v", "verdad", "t", "verdadeiro"},
    "false": {"false", "falso", "f", "fa"},
}

# ---- Utilidades JSON tolerantes (comentarios/comas finales) ---------------
_JSON_TRAILING_COMMA_RE = re.compile(r",(?=\s*[}\]])")
_JSON_LINE_COMMENTS_RE = re.compile(r"^\s*//.*?$", re.MULTILINE)
_JSON_BLOCK_COMMENTS_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

def _json_load_tolerant(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _JSON_BLOCK_COMMENTS_RE.sub("", raw)
        cleaned = _JSON_LINE_COMMENTS_RE.sub("", cleaned)
        cleaned = _JSON_TRAILING_COMMA_RE.sub("", cleaned)
        return json.loads(cleaned)

def load_mapping(path: str | None) -> dict:
    if not path:
        return dict(DEFAULT_MAPPING)  # copia
    ext = _json_load_tolerant(path)
    # Mezcla: lo que no venga en el externo, se completa con el default
    merged = dict(DEFAULT_MAPPING)
    merged.update({k: v for k, v in ext.items() if v is not None})
    return merged

# ---- Helpers XML ----------------------------------------------------------
def get_text(node: ET.Element, xpath: str) -> str:
    if xpath == ".":
        return (node.text or "").strip()
    if xpath.startswith("@"):
        return (node.attrib.get(xpath[1:], "") or "").strip()
    found = node.find(xpath)
    if found is None:
        return ""
    parts = []
    if found.text:
        parts.append(found.text)
    for child in list(found):
        if child.text:
            parts.append(child.text)
        if child.tail:
            parts.append(child.tail)
    return ("".join(parts) or "").strip()

def truthy(value: str, true_values):
    return value.strip().lower() in {v.lower() for v in true_values}

class Choice:
    def __init__(self, text: str, correct: bool, feedback: str = ""):
        self.text = text
        self.correct = correct
        self.feedback = feedback

class Question:
    def __init__(self, title: str, text: str, format_: str, choices: List[Choice], general_feedback: str = ""):
        self.title = title or text[:60]
        self.text = text
        self.format = format_
        self.choices = choices
        self.general_feedback = general_feedback

    def is_truefalse(self) -> bool:
        if len(self.choices) != 2:
            return False
        labels = {c.text.strip().lower() for c in self.choices}
        norm = set()
        for s in labels:
            s = s.strip().lower()
            if s in TRUE_FALSE_ALIASES["true"]:
                norm.add("true")
            elif s in TRUE_FALSE_ALIASES["false"]:
                norm.add("false")
            else:
                norm.add(s)
        return norm == {"true", "false"}

    def is_single(self) -> bool:
        return sum(1 for c in self.choices if c.correct) == 1

# ---- Parser SWAD con normalización de XPaths ------------------------------
def parse_swad(xml_path: str, mapping: dict) -> List[Question]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    qpath = mapping.get("question_xpath", ".//question")
    # Normaliza para evitar "cannot use absolute path on element" (Py 3.12)
    if qpath.startswith("//"):
        nodes = root.findall("." + qpath)       # "//q" -> ".//q"
    elif qpath.startswith("/"):
        nodes = tree.findall(qpath)             # ruta absoluta desde el doc
    else:
        nodes = root.findall(qpath)             # relativa

    questions: List[Question] = []
    for qnode in nodes:
        title = get_text(qnode, mapping["title"])
        qtext = get_text(qnode, mapping["text"])
        ans_nodes = qnode.findall(mapping["answer_list"])
        choices: List[Choice] = []
        for an in ans_nodes:
            atext = get_text(an, mapping["answer_text"])
            flag = get_text(an, mapping["answer_is_correct"])
            is_correct = truthy(flag, mapping["true_values"])
            fb = ""
            if mapping.get("feedback"):
                fb = get_text(an, mapping["feedback"])
            choices.append(Choice(atext, is_correct, fb))
        gfb = ""
        if mapping.get("question_feedback"):
            gfb = get_text(qnode, mapping["question_feedback"])
        questions.append(Question(title, qtext, mapping.get("text_format", "html"), choices, gfb))
    return questions

# ---- Generación Moodle/PRADO ----------------------------------------------
def build_moodle_xml_with_markers(questions: List[Question], category: str, shuffle: bool):
    quiz = ET.Element("quiz")

    # Categoría obligatoria (desde --category)
    q = ET.SubElement(quiz, "question", {"type": "category"})
    c = ET.SubElement(q, "category")
    t = ET.SubElement(c, "text"); t.text = category
    info = ET.SubElement(q, "info", {"format": "moodle_auto_format"})
    ET.SubElement(info, "text").text = ""
    ET.SubElement(q, "idnumber").text = ""

    qtext_map = {}
    for idx, q in enumerate(questions, start=1):
        qel = ET.SubElement(quiz, "question", {"type": "multichoice"})
        name = ET.SubElement(qel, "name"); ET.SubElement(name, "text").text = q.title

        qtext_el = ET.SubElement(qel, "questiontext", {"format": "html"})
        marker = f"[[QTEXT_{idx}]]"
        ET.SubElement(qtext_el, "text").text = marker
        qtext_map[marker] = f"<p>{q.text}</p>"

        if q.general_feedback:
            gf = ET.SubElement(qel, "generalfeedback", {"format": "html"})
            ET.SubElement(gf, "text").text = q.general_feedback
        else:
            gf = ET.SubElement(qel, "generalfeedback", {"format": "html"})
            ET.SubElement(gf, "text").text = ""

        ET.SubElement(qel, "defaultgrade").text = "1.0000000"
        ET.SubElement(qel, "penalty").text = "0.3333333"
        ET.SubElement(qel, "hidden").text = "0"
        ET.SubElement(qel, "idnumber").text = ""
        ET.SubElement(qel, "single").text = "true" if q.is_single() else "false"
        ET.SubElement(qel, "shuffleanswers").text = "true" if shuffle else "false"
        ET.SubElement(qel, "answernumbering").text = "abc"
        ET.SubElement(qel, "showstandardinstruction").text = "1"

        for tag in ("correctfeedback", "partiallycorrectfeedback", "incorrectfeedback"):
            fb = ET.SubElement(qel, tag, {"format": "html"})
            ET.SubElement(fb, "text").text = ""

        correct_count = max(1, sum(1 for c in q.choices if c.correct))
        fraction_each = 100 / correct_count
        for cobj in q.choices:
            frac = str(int(fraction_each)) if cobj.correct else "-25"
            a = ET.SubElement(qel, "answer", {"fraction": frac, "format": "html"})
            ET.SubElement(a, "text").text = cobj.text
            fbn = ET.SubElement(a, "feedback", {"format": "html"})
            ET.SubElement(fbn, "text").text = cobj.feedback or ""

    return quiz, qtext_map

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def serialize_with_cdata(root: ET.Element, qtext_map: dict, out_path: str):
    indent(root)
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    xml_str = xml_bytes.decode("utf-8")
    # Sustituye marcadores por CDATA
    for marker, html in qtext_map.items():
        xml_str = xml_str.replace(f"<text>{marker}</text>", f"<text><![CDATA[{html}]]></text>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

# ---- CLI ------------------------------------------------------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Convert SWAD XML to PRADO/Moodle XML (CDATA + category from --category)")
    p.add_argument("input", help="Ruta del XML exportado de SWAD")
    p.add_argument("output", help="Ruta del XML de salida (PRADO/Moodle)")
    p.add_argument("--mapping", help="JSON con el mapeo de XPaths (opcional; por defecto se usa el integrado)")
    p.add_argument("--category", required=True, help="Categoría de Moodle/PRADO para las preguntas (p.ej. $course$/top/Tema 1)")
    p.add_argument("--shuffle", choices=["true", "false"], default="true", help="Barajar respuestas en PRADO (default: true)")
    args = p.parse_args(argv)

    mapping = load_mapping(args.mapping)
    questions = parse_swad(args.input, mapping)
    if not questions:
        print("[!] No se han encontrado preguntas. Revisa 'question_xpath' en el mapping.", file=sys.stderr)
        return 2

    quiz, qtext_map = build_moodle_xml_with_markers(questions, args.category, shuffle=(args.shuffle == "true"))
    serialize_with_cdata(quiz, qtext_map, args.output)
    print(f"[✓] Convertidas {len(questions)} preguntas → {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
