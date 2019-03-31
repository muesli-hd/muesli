"""SeleniumTests for export stuff, tooltips and histograms"""
import unittest
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import muesli.web
from webtest.http import StopableWSGIServer


class SeleniumTests(unittest.TestCase):
    def setUp(self):
        app = muesli.web.main()
        self.server = StopableWSGIServer.create(app, host="127.0.0.1", port="8080")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--whitelisted-ips')
        options.add_argument('127.0.0.1')
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get("http://127.0.0.1:8080")

    def tearDown(self):
        self.server.shutdown()

    def explicit_wait_visibility(self, element):
        """
        | Waits for the visibility of the given element until the element is visible or the time limit is reached
        :param str element: String for the XPATH of the element
        :return: webdriver element
        """
        x = WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, element)))
        return x

    def explicit_wait_clickable(self, element):
        """
        | Waits for the element to be clickable until the element is clickable or the time limit is reached
        :param str element: String for the XPATH of the element
        :return: webdriver element
        """
        x = WebDriverWait(self.driver, 10).until(ec.element_to_be_clickable((By.XPATH, element)))
        return x


class SeleniumUserLoggedInTests(SeleniumTests):
    def setUp(self):
        """Use username and password to login
        """
        SeleniumTests.setUp(self)

        login_button = self.driver.find_element_by_xpath("//a[@href='/user/login']")
        login_button.click()

        email = self.driver.find_element_by_xpath("//input[@name='email']")
        password = self.driver.find_element_by_xpath("//input[@name='password'][@type='password']")

        # Login with own Admin credentials
        email.send_keys("admin@muesli.org")
        password.send_keys("adminpassword")
        login = self.driver.find_element_by_xpath("//input[@type='submit']")
        login.click()

    def test_export(self):
        """Check login and test all excel exports
        Raises:
            NoSuchElementException: Element could not be found.
        """

        # Check and click admin tab
        administration = self.explicit_wait_clickable("//a[@href='/admin']")
        administration.click()

        # Check Yaml exports
        lecture_yaml = self.explicit_wait_clickable("//a[@href='/lecture/export_yaml']")
        lecture_yaml.click()

        lecture_yaml_all = self.explicit_wait_clickable("//a[@href='/lecture/export_yaml"
                                                        "_details?show_all=1']")
        lecture_yaml_all.click()

        lecture_tutorials_yaml = self.driver.find_element_by_xpath("//a[@href='/lecture/"
                                                                   "export_yaml_details']")
        lecture_tutorials_yaml.click()

        lecture_tutorials_yaml_all = self.explicit_wait_clickable("//a[@href='/lecture/"
                                                                  "export_yaml_details?show_all=1']")
        lecture_tutorials_yaml_all.click()

        # Export all lectures and tutorials as excel file
        excel_link = self.explicit_wait_clickable("//a[@href='/lecture/export_excel/"
                                                  "downloadDetailTutorials.xlsx']")
        excel_link.click()

        # Check one lecture and grading excel export
        lectures = self.explicit_wait_clickable("//a[@href='/lecture/list']")
        lectures.click()

        lecture = self.explicit_wait_clickable("//a[@href='/lecture/view/20109']")
        lecture.click()

        lecture_edit = self.explicit_wait_clickable("//a[@href='/lecture/edit/20109']")
        lecture_edit.click()

        # Check specific grading
        gradings = self.explicit_wait_clickable("//a[@href='/grading/edit/6692']")
        gradings.click()
        grades = self.explicit_wait_clickable("//a[@href='/grading/enter_grades/6692']")
        grades.click()

        # Excel export
        excel_export = self.explicit_wait_clickable("//a[@href='/grading/export/6692.xlsx']")
        excel_export.click()

    def test_tooltips(self):
        """Check tooltips for their existence and their text
        Raises:
            NoSuchElementException: Element could not be found.
        """
        # Check lectures tab
        lectures = self.explicit_wait_clickable("//a[@href='/lecture/list']")
        lectures.click()

        # Check lecture x
        lecture = self.explicit_wait_clickable("//a[@href='/lecture/view/20109']")
        lecture.click()

        # Edit lecture x
        lecture_edit = self.explicit_wait_clickable("//a[@href='/lecture/edit/20109']")
        lecture_edit.click()

        # Check if tooltip exists and check text, variables should remain unused
        self.explicit_wait_visibility("//p[contains(text(), 'Hier können "
                                      "Noten anhand von einer oder mehreren Klausuren/"
                                      "Testaten berechnet und eingetragen werden.')]")

        self.explicit_wait_visibility("//p[contains(text(), "
                                      "'Klicken Sie auf den Namen eines "
                                      "Tutors, um ihm/ihr eine Email zu schicken.')]")

        # Check excel tooltip
        gradings = self.explicit_wait_clickable("//a[@href='/grading/edit/6692']")
        gradings.click()
        grades = self.explicit_wait_clickable("//a[@href='/grading/enter_grades/6692']")
        grades.click()

        self.explicit_wait_visibility("//p[contains(text(), 'Hier können Sie die "
                                      "Klausurergebnisse als Exceldatei (.xlsx) "
                                      "erstellen und herunterladen.')]")

    def test_histogram(self):
        """Check if histograms exist
        Raises:
            NoSuchElementException: Element could not be found.
        """
        # Check lectures tab
        lectures = self.explicit_wait_clickable("//a[@href='/lecture/list']")
        lectures.click()

        # Check lecture x
        lecture = self.explicit_wait_clickable("//a[@href='/lecture/view/20109']")
        lecture.click()

        # Edit lecture x
        lecture_edit = self.explicit_wait_clickable("//a[@href='/lecture/edit/20109']")
        lecture_edit.click()

        # Check histogram
        statistics = self.explicit_wait_clickable("//a[@href='/exam/statistics/13417/']")
        statistics.click()

        self.explicit_wait_visibility("//img[@src='/exam/histogram_for_exam/13417/']")