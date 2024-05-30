import os
import os
import pickle
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from CONSTANTS import TIMEOUT


class UnituDriver(webdriver.Edge):
    loginCalls = 0

    def __init__(self, headless=False, *args, **kwargs):
        self.headless = headless
        self.driver = self.create_driver()

        # Check if the "last_login.txt" file exists, and create it if it doesn't
        if not os.path.exists("last_login.txt"):
            with open("last_login.txt", "w") as f:
                f.write(str(0))

        # Check if the "cookies.pkl" file exists, and create it if it doesn't
        if not os.path.exists("cookies.pkl"):
            with open("cookies.pkl", "wb") as f:
                pickle.dump([], f)

    def create_driver(self):
        options = webdriver.EdgeOptions()
        if self.headless:
            options.add_argument("--headless")

        return webdriver.Edge(options=options)

    def wait_for_page_load(self):
        # TODO: Implement a better way to wait for the page to load
        time.sleep(7)

    def find_elements(self, by, value):
        def presence_of_all_elements_located(driver):
            elements = driver.find_elements(by, value)
            if len(elements) > 0:
                return elements
            else:
                return False

        return WebDriverWait(self.driver, TIMEOUT).until(
            presence_of_all_elements_located
        )

    def find_and_click(self, by, value):
        try:
            # Wait until any elements are found
            element = self.find_element(by, value)

            # Click the first element if the list is not empty
            if element:
                # wait until the element is clickable
                WebDriverWait(self.driver, TIMEOUT).until(
                    EC.element_to_be_clickable((by, value))
                )
                element.click()

        except TimeoutException:
            print("No elements found within the timeout period.")
            print(f"By: {by}, Value: {value}")

    def login(self):
        try:
            # no need to check anything else if we're already logged in
            if self.is_logged_in():
                return
        except NoSuchElementException:
            pass

        self.driver.get("https://uclan.unitu.co.uk/")
        self.load_cookies()
        self.driver.get("https://uclan.unitu.co.uk/")

        # this means the cookie injection worked
        if self.is_logged_in():
            return

        # if not cookies, ask the user to please log in
        input("Please login, and press enter when done. Note that this will store your cookies locally.")

        self.dump_cookies()

    def load_cookies(self, file_name='cookies.pkl'):
        with open(file_name, "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def dump_cookies(self, file_name='cookies.pkl'):
        # add cookies to pickle file
        with open(file_name, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def grab_posts(self):
        # open
        open_div = self.driver.find_element(By.ID, "opened-drop-here")
        open_tickets = open_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        # in progress
        in_progress_div = self.driver.find_element(By.ID, "in-progress-drop-here")
        in_progress_tickets = in_progress_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        # closed
        closed_div = self.driver.find_element(By.ID, "closed-drop-here")
        closed_tickets = closed_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        print("Open tickets: ")
        for ticket in open_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            print(a_tag.get_attribute("href"))

        print("In Progress tickets: ")
        for ticket in in_progress_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            print(a_tag.get_attribute("href"))

        print("Closed tickets: ")
        for ticket in closed_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            print(a_tag.get_attribute("href"))

    def is_logged_in(self):
        username = self.driver.find_element(By.CSS_SELECTOR, ".menu-username")

        return bool(username)

    def get(self, url):
        self.driver.get(url)
        # self.wait_for_page_load()

    def find_element(self, by, value):
        return WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((by, value))
        )

    def get_driver(self):
        return self.driver

    def close(self):
        self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, item):
        """
        Delegate attribute access to the underlying WebDriver if it's not part of this class.
        This modification ensures that properties and methods from selenium-wire are accessible.
        """
        # The following line ensures that properties like `requests` are properly managed
        attr = getattr(self.driver, item)
        if callable(attr):
            return attr
        else:
            return attr
