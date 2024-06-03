from UnituDriver import UnituDriver

if __name__ == '__main__':
    driver = UnituDriver(
        headless=True
    )

    driver.login()

    urls = driver.get_all_board_urls()

    for url in urls:
        driver.grab_active_posts(url)
        driver.grab_archived_posts(url)

    driver.dump_json()

    # # store the html of the page to a file
    # with open("file.html", "w") as f:
    #     f.write(driver.page_source)
