import json
import os
import pickle
import time

import requests
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
        self.headless_client = self.create_headless_client()

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
            # force window to 1080p
            options.add_argument("window-size=1920,1080")
            options.add_argument("--headless")
        return webdriver.Edge(options=options)

    def create_headless_client(self):
        session = requests.Session()
        cookies = self.load_cookies()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        return session

    def load_cookies(self, file_name='cookies.pkl'):
        with open(file_name, "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
        return cookies

    def dump_cookies(self, file_name='cookies.pkl'):
        # add cookies to pickle file
        with open(file_name, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def wait_for_page_load(self):
        # TODO: Implement a better way to wait for the page to load
        time.sleep(1)

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
                print("Logged in already, likely redundant login call")
                return
        except Exception:
            pass

        self.driver.get("https://uclan.unitu.co.uk/")
        cookies = self.load_cookies()

        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.get("https://uclan.unitu.co.uk/")

        # this means the cookie injection worked
        if self.is_logged_in():
            print("Cookies injected successfully")
            return

        # if not cookies, ask the user to please log in
        input("Please login, and press enter when done. Note that this will store your cookies locally.")

        self.dump_cookies()

    def dump_json(self, file_name='data.json'):
        if len(self.data) == 0:
            print("Nothing to dump. Aborting")
            return

        with open(file_name, "w") as f:
            json.dump(self.data, f)

        print(f"Data written to: {file_name}. Length of data: {len(self.data)}")

    def scrape_post(self, url):
        print(f"Scraping {url}")
        current_data = {}
        # Open a new tab
        # go to the url before doing anything
        self.driver.execute_script(f"window.open('{url}');")
        # Switch context to the new tab
        self.driver.switch_to.window(self.driver.window_handles[1])
        post_id = url.split('-')[-1]

        current_data["boardName"] = self.extract_text(".menu-links-selected", by=By.CSS_SELECTOR)
        current_data["title"] = self.extract_text("feedbackTitle", by=By.ID)

        current_data["description"] = self.extract_text("feedbackDescription", by=By.ID)
        if not bool(current_data["description"]):
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

        current_data["feedbackCategory"] = self.extract_text(
            "//div[contains(text(),'Feedback category')]/following-sibling::div")
        current_data["feedbackDetails"] = self.extract_text("//h6[contains(text(),'Feedback Details')]")
        current_data["type"] = self.extract_text(
            "//div[contains(text(),'Type')]/following-sibling::div/span[@data-cy='feedback-type']")
        current_data["status"] = self.extract_text("//div[contains(text(),'Status')]/following-sibling::div")
        current_data["viewed"] = \
            get_nums_from_str(self.extract_text("//div[contains(text(),'Viewed')]/following-sibling::div"))[0]

        current_data["year"] = self.extract_text("//div[contains(text(),'Year')]/following-sibling::div")
        if current_data["year"] is not None:
            nums = get_nums_from_str(current_data["year"])
            if len(nums) > 0:
                current_data["year"] = nums[0]

        current_data["module"] = self.extract_text("//div[contains(text(),'Module')]/following-sibling::div")

        current_data["assignee"] = self.extract_text("//div[contains(text(),'Assignee')]/following-sibling::div")
        if current_data["assignee"]:
            split = current_data["assignee"].split('\n')
            if len(split) > 1:
                current_data["assignee"] = split[1]
            else:
                current_data["assignee"] = split[0]

        nums = get_nums_from_str(self.extract_text("//div[contains(text(),'Staff')]/following-sibling::div"))
        if len(nums) > 0:
            current_data["staffViews"] = nums[0]

        nums = get_nums_from_str(self.extract_text("//div[contains(text(),'Students')]/following-sibling::div"))
        if len(nums) > 0:
            current_data["studentViews"] = nums[0]

        # -------------- open posts --------------
        try:
            issue_status_div = self.driver.find_element(By.XPATH, "//div[contains(text(), 'status to Open')]/..")

            current_data["issueOpenerName"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.h6").text

            small_text_element = issue_status_div.find_elements(By.CSS_SELECTOR, "span.small.text-dark-600")
            current_data["issueOpenedHowLongAgo"] = small_text_element[0].text

            if len(small_text_element) > 1:
                current_data["issueOpenerDesignation"] = small_text_element[1].text
            else:
                try:
                    print(f"Issue opener {current_data['issueOpenerName']} doesn't have a designation, {url}")
                except KeyError:
                    print("Issue opener doesn't exist in current_data, and doesn't have a designation")

            current_data["issueOpenerRole"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.badge").text

        except NoSuchElementException as e:
            print(f"unable to find all fields of open posts. assuming that post was never opened.")

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

                current_data["issueCloserName"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.h6").text

                small_text_element = issue_status_div.find_elements(By.CSS_SELECTOR, "span.small.text-dark-600")
                if len(small_text_element) >= 2:
                    current_data["issueClosedHowLongAgo"] = small_text_element[0].text
                    current_data["issueCloserDesignation"] = small_text_element[1].text

                current_data["issueCloserRole"] = issue_status_div.find_element(By.CSS_SELECTOR, "span.badge").text
            except NoSuchElementException as e:
                print(f"unable to find all fields of closed posts. Exception: {e}")

        current_data["unituUrl"] = url

        current_data["comments"] = self.grab_post_comments()

        # ensure that there are no values that are None
        keys_to_remove = [key for key, value in current_data.items() if value is None]
        for key in keys_to_remove:
            del current_data[key]

        # save the data to the object
        self.data.append(current_data)

        # close this tab
        self.driver.close()
        # switch context to the first tab
        self.driver.switch_to.window(self.driver.window_handles[0])

        return current_data

    def collect_data(self):
        return self.data

    def get_all_board_urls(self):
        scrollable_menu = self.driver.find_element(By.CSS_SELECTOR, "#departmentsScrollableMenu")

        boards = scrollable_menu.find_elements(By.XPATH, ".//li[contains(@class, 'menu-link-item')]")

        urls = []
        for board in boards:
            a_tag = board.find_element(By.TAG_NAME, "a")

            urls.append(a_tag.get_attribute("href"))

        return urls

    def grab_archived_post_urls(self, board_url, limit=-1):
        home_url = "https://uclan.unitu.co.uk"

        # go to the url of the board before getting the posts
        # self.driver.get(board_url)

        # Click on the archive page link
        self.driver.find_element(By.CSS_SELECTOR, "a[data-cy='archive-page']").click()

        # Wait for the page to load fully
        # self.wait_for_page_load()

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

        urls = []
        # Iterate over the selected archived tickets
        for ticket in archived_tickets:
            ticket_href = ticket.get_attribute("href")

            if not ticket_href:
                continue

            ticket_full_url = f"{home_url}{ticket_href}"
            urls.append(ticket_full_url)

        return urls

    def grab_active_post_urls(self, board_url, limit=-1):
        def process_tickets(tickets):
            # Determine the number of posts to process based on the limit
            if limit != -1 and limit <= len(tickets):
                return tickets[:limit]
            return tickets

        def get_href(tickets):
            urls = []

            for ticket in tickets:
                a_tag = ticket.find_element(By.TAG_NAME, "a")
                urls.append(a_tag.get_attribute("href"))

            return urls

        # go to the url of the board before getting the posts
        self.driver.get(board_url)

        # open
        open_div = self.driver.find_element(By.ID, "opened-drop-here")
        open_tickets = open_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        open_tickets = process_tickets(open_tickets)
        open_urls = get_href(open_tickets)

        # in progress
        in_progress_div = self.driver.find_element(By.ID, "in-progress-drop-here")
        in_progress_tickets = in_progress_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        in_progress_tickets = process_tickets(in_progress_tickets)
        in_progress_urls = get_href(in_progress_tickets)

        # closed
        closed_div = self.driver.find_element(By.ID, "closed-drop-here")
        closed_tickets = closed_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        closed_tickets = process_tickets(closed_tickets)
        closed_urls = get_href(closed_tickets)

        return open_urls + in_progress_urls + closed_urls

    def grab_active_posts(self, board_url, limit=-1):
        def process_tickets(tickets):
            # Determine the number of posts to process based on the limit
            if limit != -1 and limit <= len(tickets):
                return tickets[:limit]
            return tickets

        def scrape_tickets(tickets):
            for ticket in tickets:
                a_tag = ticket.find_element(By.TAG_NAME, "a")
                self.scrape_post(a_tag.get_attribute("href"))

        # go to the url of the board before getting the posts
        self.driver.get(board_url)

        # open
        open_div = self.driver.find_element(By.ID, "opened-drop-here")
        open_tickets = open_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        open_tickets = process_tickets(open_tickets)
        scrape_tickets(open_tickets)

        # in progress
        in_progress_div = self.driver.find_element(By.ID, "in-progress-drop-here")
        in_progress_tickets = in_progress_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        in_progress_tickets = process_tickets(in_progress_tickets)
        scrape_tickets(in_progress_tickets)

        # closed
        closed_div = self.driver.find_element(By.ID, "closed-drop-here")
        closed_tickets = closed_div.find_elements(By.CSS_SELECTOR, ".feedback-ticket")
        closed_tickets = process_tickets(closed_tickets)
        scrape_tickets(closed_tickets)

    def grab_archived_posts(self, board_url, limit=-1):
        home_url = "https://uclan.unitu.co.uk"

        # go to the url of the board before getting the posts
        self.driver.get(board_url)

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
                continue

            ticket_full_url = f"{home_url}{ticket_href}"
            self.scrape_post(ticket_full_url)

    def grab_post_comments(self):
        comment_list = self.driver.find_elements(By.XPATH, "//*[@id='feedbackComments']/*")
        comments = []

        if len(comment_list) <= 0:
            return comments

        for comment in comment_list:
            curr_comment = {}

            try:
                content_element = comment.find_element(By.XPATH, ".//div[contains(@id, 'full_text_comment')]")
            except NoSuchElementException:
                try:
                    content_element = comment.find_element(By.TAG_NAME, "em")
                    print("Removed Comment found!")
                except NoSuchElementException:
                    # this means that there are no comments.
                    print("No comments on post")
                    continue

                curr_comment["content"] = content_element.text

                if curr_comment.get("removed_count"):
                    curr_comment["removed_count"] += 1
                else:
                    curr_comment["removed_count"] = 1

                comments.append(curr_comment)

                continue

            curr_comment["content"] = content_element.get_attribute("innerHTML").strip()
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
        try:
            username = self.driver.find_element(By.CSS_SELECTOR, ".menu-username")
        except Exception as e:
            return False

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
