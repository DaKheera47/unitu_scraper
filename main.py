from UnituDriver import UnituDriver

if __name__ == '__main__':
    driver = UnituDriver(
        headless=False
    )

    driver.login()

    # driver.grab_active_posts()
    driver.grab_archived_posts(limit=5)

    print(driver.get_data())

    # # store the html of the page to a file
    # with open("file.html", "w") as f:
    #     f.write(driver.page_source)
