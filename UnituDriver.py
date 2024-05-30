import os
import os
import pickle
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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

    def login(self, future_url=None):
        self.loginCalls += 1

        self.driver.get("https://www.bokea.co/gestion/login")

        # if the last time the driver was login was more than 30 minutes ago, log in again
        with open("last_login.txt", "r") as f:
            last_used = float(f.read())
            if time.time() - last_used < 1800:
                # add cookies from pickle file
                with open("cookies.pkl", "rb") as cookie_file:
                    cookies = pickle.load(cookie_file)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)

                # either try going to the future url or refresh the page
                if future_url:
                    self.driver.get(future_url)
                else:
                    self.driver.refresh()
                return

        login_field = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "loginName"))
        )
        password_field = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        login_field.send_keys(self.username)
        password_field.send_keys(self.password + Keys.ENTER)

        self.wait_for_page_load()

        # add cookies to pickle file
        with open("cookies.pkl", "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

        # make a log file to store when the last time the driver was used
        with open("last_login.txt", "w") as f:
            f.write(str(time.time()))

    def load_cookies(self, file_name='cookies.pkl'):
        with open(file_name, "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def dump_cookies(self, file_name='cookies.pkl'):
        # add cookies to pickle file
        with open(file_name, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

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
