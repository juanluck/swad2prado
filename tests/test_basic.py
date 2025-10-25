import os
import subprocess
import xml.etree.ElementTree as ET
import unittest
import re

BASE = os.path.dirname(os.path.dirname(__file__))
SCRIPT = os.path.join(BASE, "swad2prado.py")
MAPPING = os.path.join(BASE, "mapping.json")
SWAD = os.path.join(BASE, "examples", "swad.xml")
OUT = os.path.join(BASE, "examples", "output", "prado_out_test.xml")
CATEGORY = "$course$/top/Banco importado desde SWAD (CI)"

class TestConversion(unittest.TestCase):
    def test_cli_and_output(self):
        # Run converter
        if os.path.exists(OUT):
            os.remove(OUT)
        cmd = [ "python", SCRIPT, SWAD, OUT, "--mapping", MAPPING, "--category", CATEGORY, "--shuffle", "true" ]
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists(OUT), "Se esperaba el XML de salida")

        # Parse output
        tree = ET.parse(OUT)
        root = tree.getroot()

        # Category present
        cat = root.find(".//question[@type='category']/category/text")
        self.assertIsNotNone(cat, "Debe haber una categoría")
        self.assertEqual(cat.text, CATEGORY)

        # Count questions equals to input questions
        in_qs = ET.parse(SWAD).getroot().findall(".//question")
        out_qs = root.findall(".//question[@type='multichoice']")
        self.assertEqual(len(in_qs), len(out_qs), "Número de preguntas debe coincidir")

        # CDATA with <p> is present inside questiontext/text
        xml_text = open(OUT, "r", encoding="utf-8").read()
        self.assertRegex(xml_text, r"<questiontext[^>]*>\s*<text><!\[CDATA\[<p>.*?</p>\]\]></text>", "Debe haber CDATA con <p>…</p>")

        # Wrong answers get -25; at least one occurrence
        self.assertIn('fraction="-25"', xml_text, "Las incorrectas deben tener fraction=-25")

if __name__ == "__main__":
    unittest.main()
