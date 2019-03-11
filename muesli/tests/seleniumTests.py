"""SeleniumTests for export stuff, tooltips and histograms"""
import time
from selenium import webdriver


def initiate_driver(user, key):
    """Initiate Chrome Webdriver with path to chromedriver and address localhost:8080

    Args:
        user: E-mail address of muesli user
        key: Pasword of muesli user

    Returns:
        Chrome Webdriver with a logged in (admin) user for the muesli page
    """
    driver = webdriver.Chrome("SeleniumDriver/chromedriver")
    driver.maximize_window()
    driver.get("localhost:8080")

    login_button = driver.find_element_by_xpath("//a[@href='/user/login']")
    login_button.click()

    email = driver.find_element_by_xpath("//input[@name='email']")
    password = driver.find_element_by_xpath("//input[@name='password'][@type='password']")

    # Login with own Admin credentials
    email.send_keys(user)
    password.send_keys(key)
    login = driver.find_element_by_xpath("//input[@type='submit']")
    login.click()

    return driver


def export_test():
    """Check login and test all excel exports
    Raises:
        NoSuchElementException: Element could not be found.
    """
    driver = initiate_driver("dennis.pfleger@web.de", "a")

    # Wait for page to load
    time.sleep(2)

    # Check and click admin tab
    administration = driver.find_element_by_xpath("//a[@href='/admin']")
    administration.click()

    # Check Yaml exports
    lecture_yaml = driver.find_element_by_xpath("//a[@href='/lecture/export_yaml']")
    lecture_yaml.click()

    lecture_yaml_all = driver.find_element_by_xpath("//a[@href='/lecture/export_yaml"
                                                    "_details?show_all=1']")
    lecture_yaml_all.click()

    lecture_tutorials_yaml = driver.find_element_by_xpath("//a[@href='/lecture/"
                                                          "export_yaml_details']")
    lecture_tutorials_yaml.click()

    lecture_tutorials_yaml_all = driver.find_element_by_xpath("//a[@href='/lecture/"
                                                              "export_yaml_details?show_all=1']")
    lecture_tutorials_yaml_all.click()

    # Export all lectures and tutorials as excel file
    excel_link = driver.find_element_by_xpath("//a[@href='/lecture/export_excel/"
                                             "downloadDetailTutorials.xlsx']")
    excel_link.click()

    # Check one lecture and grading excel export
    lectures = driver.find_element_by_xpath("//a[@href='/lecture/list']")
    lectures.click()

    lecture = driver.find_element_by_xpath("//a[@href='/lecture/view/20109']")
    lecture.click()

    lecture_edit = driver.find_element_by_xpath("//a[@href='/lecture/edit/20109']")
    lecture_edit.click()

    # Check specific grading
    gradings = driver.find_element_by_xpath("//a[@href='/grading/edit/6692']")
    gradings.click()
    grades = driver.find_element_by_xpath("//a[@href='/grading/enter_grades/6692']")
    grades.click()

    # Excel export
    excel_export = driver.find_element_by_xpath("//a[@href='/grading/export/6692.xlsx']")
    excel_export.click()

    time.sleep(3)


def check_tooltips():
    """Check tooltips for their existence and their text
    Raises:
        NoSuchElementException: Element could not be found.
    """
    driver = initiate_driver("dennis.pfleger@web.de", "a")

    # Wait for page to load
    time.sleep(2)

    # Check lectures tab
    lectures = driver.find_element_by_xpath("//a[@href='/lecture/list']")
    lectures.click()

    # Check lecture x
    lecture = driver.find_element_by_xpath("//a[@href='/lecture/view/20109']")
    lecture.click()

    # Edit lecture x
    lecture_edit = driver.find_element_by_xpath("//a[@href='/lecture/edit/20109']")
    lecture_edit.click()

    # Check if tooltip exists and check text, variables should remain unused
    tooltip_grading = driver.find_element_by_xpath("//p[contains(text(), 'Hier können "
                                                  "Noten anhand von einer oder mehreren Klausuren/"
                                                  "Testaten berechnet und eingetragen werden.')]")

    tooltip_tutor = driver.find_element_by_xpath("//p[contains(text(), "
                                                 "'Klicken Sie auf den Namen eines "
                                                "Tutors, um ihm/ihr eine Email zu schicken.')]")

    # Check excel tooltip
    gradings = driver.find_element_by_xpath("//a[@href='/grading/edit/6692']")
    gradings.click()
    grades = driver.find_element_by_xpath("//a[@href='/grading/enter_grades/6692']")
    grades.click()

    excel_tooltip = driver.find_element_by_xpath("//p[contains(text(), 'Hier können Sie die "
                                                "Klausurergebnisse als Exceldatei (.xlsx) "
                                                 "erstellen und herunterladen.')]")

    time.sleep(3)


def histogram_test():
    """Check if histograms exist
    Raises:
        NoSuchElementException: Element could not be found.
    """
    driver = initiate_driver("dennis.pfleger@web.de", "a")

    # Wait for page to load
    time.sleep(2)

    # Check lectures tab
    lectures = driver.find_element_by_xpath("//a[@href='/lecture/list']")
    lectures.click()

    # Check lecture x
    lecture = driver.find_element_by_xpath("//a[@href='/lecture/view/20109']")
    lecture.click()

    # Edit lecture x
    lecture_edit = driver.find_element_by_xpath("//a[@href='/lecture/edit/20109']")
    lecture_edit.click()

    # Check histogram
    statistics = driver.find_element_by_xpath("//a[@href='/exam/statistics/13417/']")
    statistics.click()

    # Wait for histogram to load and get it
    time.sleep(2)
    driver.find_element_by_xpath("//img[@src='/exam/histogram_for_exam/13417/']")

    time.sleep(3)


if __name__ == "__main__":
    export_test()
    check_tooltips()
    histogram_test()
