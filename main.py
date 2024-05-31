from UnituDriver import UnituDriver

if __name__ == '__main__':
    driver = UnituDriver(
        headless=True
    )

    driver.login()

    driver.grab_posts()

    print(driver.get_data())

    # # store the html of the page to a file
    # with open("file.html", "w") as f:
    #     f.write(driver.page_source)
