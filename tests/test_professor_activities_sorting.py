import importlib.util
import unittest
from pathlib import Path

from bs4 import BeautifulSoup


MODULE_PATH = Path(__file__).resolve().parents[1] / "scrape-professor-news.py"
SPEC = importlib.util.spec_from_file_location("scrape_professor_news", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProfessorActivitiesSortingTests(unittest.TestCase):
    def make_table(self, rows):
        rows_html = "".join(
            f"<tr><td>{code}</td><td>{teaching}</td><td>{year}</td>"
            f"<td>{semester}</td><td>{language}</td><td>{course}</td>"
            f"<td>{course_code}</td><td>{curriculum}</td></tr>"
            for code, teaching, year, semester, language, course, course_code, curriculum in rows
        )
        soup = BeautifulSoup(
            "<div><table><thead><tr>"
            "<th>Code</th><th>Teaching</th><th>Year</th><th>Semester</th>"
            "<th>Language</th><th>Course</th><th>Course Code</th><th>Curriculum</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
            "html.parser",
        )
        return soup, soup.div

    def row_values(self, content_div):
        return [
            [cell.get_text(" ", strip=True) for cell in row.find_all("td", recursive=False)]
            for row in content_div.select("tbody > tr")
        ]

    def test_sorts_by_teaching_then_course_case_insensitively(self):
        rows = [
            ("3", "Zoologia", "1", "2", "ITA", "Biologia", "30", "C"),
            ("2", "algebra", "1", "1", "ITA", "Matematica", "20", "B"),
            ("1", "Algebra", "1", "1", "ITA", "Informatica", "10", "A"),
        ]
        soup, content_div = self.make_table(rows)

        MODULE.optimize_activities_table(soup, content_div)

        values = self.row_values(content_div)
        self.assertEqual(
            [(row[0].split(" (")[0], row[3].split(" (")[0]) for row in values],
            [("Algebra", "Informatica"), ("algebra", "Matematica"), ("Zoologia", "Biologia")],
        )

    def test_sorts_by_curriculum_when_teaching_and_course_match(self):
        rows = [
            ("3", "Intelligenza Artificiale", "3", "2", "ITA", "Informatica", "33503", "Tecnologico"),
            ("2", "Intelligenza Artificiale", "3", "2", "ITA", "Informatica", "33503", "metodologico"),
            ("1", "Intelligenza Artificiale", "3", "2", "ITA", "Informatica", "33503", "Curriculum unico"),
        ]
        soup, content_div = self.make_table(rows)

        MODULE.optimize_activities_table(soup, content_div)

        curricula = [row[4] for row in self.row_values(content_div)]
        self.assertEqual(curricula, ["Curriculum unico", "metodologico", "Tecnologico"])

    def test_output_is_identical_for_different_source_orders(self):
        rows = [
            ("2", "Analisi", "2", "1", "ITA", "Matematica", "20", "Curriculum B"),
            ("1", "Analisi", "1", "2", "ITA", "Matematica", "10", "Curriculum A"),
            ("3", "Geometria", "1", "1", "ITA", "Fisica", "30", "Curriculum C"),
        ]
        outputs = []
        for source_rows in (rows, list(reversed(rows))):
            soup, content_div = self.make_table(source_rows)
            MODULE.optimize_activities_table(soup, content_div)
            outputs.append(str(content_div))

        self.assertEqual(outputs[0], outputs[1])


    def test_forces_italian_names_for_computer_science_courses(self):
        rows = [
            (
                "2",
                "Remote course",
                "1",
                "1",
                "ENG",
                "Computer Science - delivered predominantly via distance learning",
                "33504",
                "A",
            ),
            ("1", "Local course", "1", "1", "ENG", "Computer Science", "33503", "B"),
        ]
        soup, content_div = self.make_table(rows)

        MODULE.optimize_activities_table(soup, content_div)

        courses = [
            row.find_all("td", recursive=False)[3].get_text(" ", strip=True)
            for row in content_div.select("tbody > tr")
        ]
        self.assertEqual(
            courses,
            [
                "Informatica ( 33503 )",
                "Informatica - erogato in modalità prevalentemente a distanza ( 33504 )",
            ],
        )

    def test_does_not_override_other_course_names(self):
        rows = [
            ("1", "Algorithms", "1", "1", "ENG", "Bioinformatics", "33455", "A"),
        ]
        soup, content_div = self.make_table(rows)

        MODULE.optimize_activities_table(soup, content_div)

        course = content_div.select_one("tbody > tr").find_all("td", recursive=False)[3]
        self.assertEqual(course.get_text(" ", strip=True), "Bioinformatics ( 33455 )")

    def test_keeps_each_sorted_row_on_its_own_line(self):
        rows = [
            ("2", "Zoologia", "1", "1", "ITA", "Biologia", "20", "B"),
            ("1", "Algebra", "1", "1", "ITA", "Matematica", "10", "A"),
        ]
        soup, content_div = self.make_table(rows)

        MODULE.optimize_activities_table(soup, content_div)

        tbody_html = str(content_div.tbody)
        self.assertEqual(tbody_html.count("\n<tr>"), 2)
        self.assertNotIn("</tr><tr>", tbody_html)
        self.assertTrue(tbody_html.endswith("</tr>\n</tbody>"))

    def test_leaves_unrelated_tables_unchanged(self):
        soup = BeautifulSoup(
            "<div><table><tbody><tr><td>B</td></tr><tr><td>A</td></tr></tbody></table></div>",
            "html.parser",
        )
        before = str(soup.div)

        MODULE.optimize_activities_table(soup, soup.div)

        self.assertEqual(str(soup.div), before)


if __name__ == "__main__":
    unittest.main()
