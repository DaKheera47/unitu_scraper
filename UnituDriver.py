import json
import os
import pickle
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from CONSTANTS import TIMEOUT
from utils import get_nums_from_str


class UnituDriver(webdriver.Edge):
    loginCalls = 0

    def __init__(self, headless=False, *args, **kwargs):
        self.headless = headless
        self.data = []
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
        time.sleep(2)

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

    def extract_text(self, selector, by=By.XPATH):
        try:
            return self.driver.find_element(by, selector).text
        except NoSuchElementException:
            return None

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

    def scrape_post(self, url):
        current_data = {}
        # Open a new tab
        self.driver.execute_script("window.open('');")
        # Switch context to the new tab
        self.driver.switch_to.window(self.driver.window_handles[1])
        post_id = url.split('-')[-1]

        self.driver.get(url)

        current_data["title"] = self.extract_text("feedbackTitle", by=By.ID)
        try:
            # required for descriptions that don't expand
            current_data["description"] = self.extract_text("feedbackDescription", by=By.ID)
        except NoSuchElementException:
            # required for descriptions that expand with a "show more" button
            description_element = self.driver.find_element(By.ID, f"full_description_{post_id}")
            current_data["description"] = description_element.get_attribute('innerHTML').strip()

        try:
            upvote_element = self.driver.find_element(By.ID, f"countPositive_{post_id}")
        except NoSuchElementException:
            upvote_element = self.driver.find_elements(By.CSS_SELECTOR, f".btn.btn-white.text-dark-600.pe-none")[0]
        current_data["upvotes"] = get_nums_from_str(upvote_element.text)[0]

        try:
            downvote_element = self.driver.find_element(By.ID, f"countNegative_{post_id}")
        except NoSuchElementException:
            downvote_element = self.driver.find_elements(By.CSS_SELECTOR, f".btn.btn-white.text-dark-600.pe-none")[1]
        current_data["downvotes"] = get_nums_from_str(downvote_element.text)[0]

        current_data["timer"] = self.extract_text("feedback-timer", by=By.ID)

        current_data["feedback_category"] = self.extract_text(
            "//div[contains(text(),'Feedback category')]/following-sibling::div")
        current_data["feedback_details"] = self.extract_text("//h6[contains(text(),'Feedback Details')]")
        current_data["type"] = self.extract_text(
            "//div[contains(text(),'Type')]/following-sibling::div/span[@data-cy='feedback-type']")
        current_data["status"] = self.extract_text("//div[contains(text(),'Status')]/following-sibling::div")
        current_data["viewed"] = self.extract_text("//div[contains(text(),'Viewed')]/following-sibling::div")
        current_data["year"] = self.extract_text("//div[contains(text(),'Year')]/following-sibling::div")
        current_data["module"] = self.extract_text("//div[contains(text(),'Module')]/following-sibling::div")
        current_data["assignee"] = \
            self.extract_text("//div[contains(text(),'Assignee')]/following-sibling::div").split('\n')[1]

        current_data["staff_views"] = self.extract_text("//div[contains(text(),'Staff')]/following-sibling::div")
        current_data["student_views"] = self.extract_text("//div[contains(text(),'Students')]/following-sibling::div")

        # -------------- open posts --------------
        try:
            issue_status_div = self.driver.find_element(By.XPATH, "//div[contains(text(), 'status to Open')]/..")

            current_data["issue_opener_name"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.h6").text

            small_text_element = issue_status_div.find_elements(By.CSS_SELECTOR, "span.small.text-dark-600")
            current_data["issue_opened_how_long_ago"] = small_text_element[0].text

            if len(small_text_element) > 1:
                current_data["issue_opener_designation"] = small_text_element[1].text
            else:
                print(f"issue opener {current_data['issue_opener_name']} doesn't have a designation, {url}")

            current_data["issue_opener_role"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.badge").text
        except NoSuchElementException as e:
            print(f"unable to find all fields of open posts. Exception: {e}")

        # -------------- closed and archived posts --------------
        if current_data["status"] == "Closed" or current_data["status"] == "Archived":
            try:
                divs_with_close = self.driver.find_elements(By.XPATH, "*//div[contains(text(), 'Closed')]/..")

                if len(divs_with_close) <= 0:
                    raise NoSuchElementException(msg="no divs with 'closed' in it")

                issue_status_div = None
                for div in divs_with_close:
                    # Find the div that's also a feedback-history-container
                    try:
                        issue_status_div = div.find_element(By.XPATH, "..//*[@data-cy='feedback-history-container']")
                    except NoSuchElementException:
                        pass

                if not issue_status_div:
                    print("unable to find div with 'Closed' and @data-cy='feedback-history-container'")
                    raise NoSuchElementException(msg="unable to find all fields of closed posts")

                current_data["issue_closer_name"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.h6").text

                small_text_element = issue_status_div.find_elements(By.CSS_SELECTOR, "span.small.text-dark-600")
                current_data["issue_closed_how_long_ago"] = small_text_element[0].text
                current_data["issue_closer_designation"] = small_text_element[1].text

                current_data["issue_closer_role"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.badge").text
            except NoSuchElementException as e:
                print(f"unable to find all fields of closed posts. Exception: {e}")

        current_data["unitu_url"] = url

        current_data["comments"] = self.grab_post_comments()

        # save the data to the object
        self.data.append(current_data)

        # close this tab
        self.driver.close()
        # switch context to the first tab
        self.driver.switch_to.window(self.driver.window_handles[0])

    def get_data(self):
        return self.data

    def grab_active_posts(self):
        # open
        open_div = self.driver.find_element(By.ID, "opened-drop-here")
        open_tickets = open_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        # in progress
        in_progress_div = self.driver.find_element(By.ID, "in-progress-drop-here")
        in_progress_tickets = in_progress_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        # closed
        closed_div = self.driver.find_element(By.ID, "closed-drop-here")
        closed_tickets = closed_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")

        for ticket in open_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            self.scrape_post(a_tag.get_attribute("href"))

        for ticket in in_progress_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            self.scrape_post(a_tag.get_attribute("href"))

        for ticket in closed_tickets:
            a_tag = ticket.find_element(By.TAG_NAME, "a")
            self.scrape_post(a_tag.get_attribute("href"))

    def grab_archived_posts(self, limit=-1):
        home_url = "https://uclan.unitu.co.uk"

        # Click on the archive page link
        self.driver.find_element(By.CSS_SELECTOR, "a[data-cy='archive-page']").click()

        # Wait for the page to load fully
        self.wait_for_page_load()

        # Get all the archived tickets
        archived_tickets = \
            self.driver.find_elements(By.XPATH,
                                      "*//div[contains(@class, 'archive-block__name')]/following-sibling::div/*")

        # Determine the number of posts to process based on the limit
        if limit != -1 and limit <= len(archived_tickets):
            # Process up to 'limit' tickets if a valid limit is specified
            archived_tickets = archived_tickets[:limit]
        else:
            # If limit is -1 or greater than the number of tickets, process all tickets
            archived_tickets = archived_tickets

        # Iterate over the selected archived tickets
        for ticket in archived_tickets:
            ticket_href = ticket.get_attribute("href")
            if not ticket_href:
                print(ticket.get_attribute("innerHTML"))
                print("unable to find ticket href")
                continue
            ticket_full_url = f"{home_url}{ticket_href}"
            print(ticket_full_url)
            self.scrape_post(ticket_full_url)

    def grab_post_comments(self):
        comment_list = self.driver.find_elements(By.XPATH, "//*[@id='feedbackComments']/*")
        comments = []

        for comment in comment_list:
            curr_comment = {}

            curr_comment["content"] = comment.find_element(By.XPATH, ".//div[contains(@id, 'full_text_comment')]").text
            curr_comment["author"] = \
                comment.find_element(By.XPATH, ".//span[contains(@data-cy, 'feedback-author-full-name')]").text
            parent = comment.find_element(By.XPATH,
                                          ".//descendant-or-self::div[contains(@data-cy, 'comment-author')]/..")
            child = parent.find_elements(By.TAG_NAME, "div")[1]
            child_spans = child.find_elements(By.TAG_NAME, "span")

            if len(child_spans) > 0:
                if bool(child_spans[0].text):
                    curr_comment["role"] = child_spans[0].text
                if bool(child_spans[1].text):
                    curr_comment["designation"] = child_spans[1].text

            comments.append(curr_comment)

        return comments

    def is_logged_in(self):
        username = self.driver.find_element(By.CSS_SELECTOR, ".menu-username")

        # does the username field exist on the page
        # it only exists when logged in
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
