from UnituDriver import UnituDriver

if __name__ == '__main__':
    driver = UnituDriver(
        headless=True
    )

    driver.login()

    driver.grab_active_posts()
    driver.grab_archived_posts()

    driver.collect_data()

    driver.dump_json()

    # # store the html of the page to a file
    # with open("file.html", "w") as f:
    #     f.write(driver.page_source)
