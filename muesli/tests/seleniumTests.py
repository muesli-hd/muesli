from selenium import webdriver
import time

def initDriver():
    driver = webdriver.Chrome("SeleniumDriver/chromedriver")
    driver.get("https://localhost:8080")

    return driver

def excelTest():
    driver = initDriver()
    driver.get("localhost:8080")

    loginBut = driver.find_element_by_xpath("//a[@href='/user/login']")
    loginBut.click()

    email = driver.find_element_by_xpath("//input[@name='email']")
    pw = driver.find_element_by_xpath("//input[@name='password'][@type='password']")

    email.send_keys("dennis.pfleger@web.de")
    pw.send_keys("a")
    ĺogin = driver.find_element_by_xpath("//input[@type='submit']").click()

    #wait for page to load
    time.sleep(2)

    #Check admin tab
    administration = driver.find_element_by_xpath("//a[@href='/admin']")
    administration.click()

    #Export all lectures and tutorials as excel file
    excelLink = driver.find_element_by_xpath("//a[@href='/lecture/export_excel/downloadDetailTutorials.xlsx']")
    excelLink.click()

    #Check one lecture and grading excel export
    lectures = driver.find_element_by_xpath("//a[@href='/lecture/list']")
    lectures.click()

    lecture = driver.find_element_by_xpath("//a[@href='/lecture/view/20109']")
    lecture.click()

    lectureEdit = driver.find_element_by_xpath("//a[@href='/lecture/edit/20109']")
    lectureEdit.click()

    #Check specific grading
    gradings = driver.find_element_by_xpath("//a[@href='/grading/edit/6692']")
    gradings.click()
    grades = driver.find_element_by_xpath("//a[@href='/grading/enter_grades/6692']")
    grades.click()

    #excel export
    excelExport = driver.find_element_by_xpath("//a[@href='/grading/export/Pruefung%206692.xlsx']")
    excelExport.click()

    time.sleep(3)

def checkTooltips():
    driver = initDriver()
    driver.get("localhost:8080")

    loginBut = driver.find_element_by_xpath("//a[@href='/user/login']")
    loginBut.click()

    email = driver.find_element_by_xpath("//input[@name='email']")
    pw = driver.find_element_by_xpath("//input[@name='password'][@type='password']")

    email.send_keys("dennis.pfleger@web.de")
    pw.send_keys("a")
    ĺogin = driver.find_element_by_xpath("//input[@type='submit']").click()

    # wait for page to load
    time.sleep(2)

    # Check lectures tab
    lectures = driver.find_element_by_xpath("//a[@href='/lecture/list']")
    lectures.click()

    #Check lecture x
    lecture = driver.find_element_by_xpath("//a[@href='/lecture/view/20109']")
    lecture.click()

    #Edit lecture x
    lecture_edit = driver.find_element_by_xpath("//a[@href='/lecture/edit/20109']")
    lecture_edit.click()

    #Check if tooltip exists and check text
    tooltipGrading = driver.find_element_by_xpath("//p[contains(text(), 'Hier können Noten anhand von einer oder "
                                                  "mehreren Klausuren/Testaten berechnet und eingetragen werden.')]")

    tooltipTutor = driver.find_element_by_xpath("//p[contains(text(), 'Klicken Sie auf den Namen eines Tutors, um ihm/ihr eine Email zu schicken.')]")


    time.sleep(3)


def histogramTest():
    driver = initDriver()
    driver.get("localhost:8080")

    loginBut = driver.find_element_by_xpath("//a[@href='/user/login']")
    loginBut.click()

    email = driver.find_element_by_xpath("//input[@name='email']")
    pw = driver.find_element_by_xpath("//input[@name='password'][@type='password']")

    email.send_keys("dennis.pfleger@web.de")
    pw.send_keys("a")
    ĺogin = driver.find_element_by_xpath("//input[@type='submit']").click()

    # wait for page to load
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

    #Check histogram
    statistics = driver.find_element_by_xpath("//a[@href='/exam/statistics/13417/']")
    statistics.click()

    #Wait for histogram to load and get it
    time.sleep(2)
    driver.find_element_by_xpath("//img[@src='/exam/histogram_for_exam/13417/']")

    time.sleep(3)

if __name__== "__main__":
    #excelTest()
    #checkTooltips()
    histogramTest()