from UnituDriver import UnituDriver
import pickle
import time

if __name__ == '__main__':
    driver = UnituDriver(
        headless=False
    )

    driver.get("https://uclan.unitu.co.uk/")
    time.sleep(2)

    driver.load_cookies()

    time.sleep(2)

    driver.get("https://uclan.unitu.co.uk/")

    print(driver.current_url)

    input("Please login now. Press enter when you're done...")

    print(driver.current_url)

    # store the html of the page to a file
    with open("file.html", "w") as f:
        f.write(driver.page_source)
