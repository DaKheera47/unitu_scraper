import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from UnituDriver import UnituDriver


def process_board(urls):
    driver = UnituDriver(headless=HEADLESS)
    driver.login()

    data = []

    for idx, url in enumerate(urls, start=1):
        data.append(driver.scrape_post(url))

    return data


INSTANCES = 7
HEADLESS = True

if __name__ == '__main__':
    driver = UnituDriver(headless=HEADLESS)
    driver.login()

    boards = driver.get_all_board_urls()

    post_urls = []
    for idx, board in enumerate(boards, start=1):
        print(f"board {idx}/{len(boards)}")
        post_urls.extend(driver.grab_active_post_urls(board))
        post_urls.extend(driver.grab_archived_post_urls(board))

    print(f"{len(post_urls)} posts")

    # write the post_urls to a file
    with open("post_urls.txt", "w") as f:
        for url in post_urls:
            f.write(url + "\n")

    # with open("post_urls.txt", "r") as f:
    #     post_urls.extend(f.read().splitlines())

    # Divide the URLs into INSTANCES segments
    segments = [post_urls[i::INSTANCES] for i in range(INSTANCES)]

    all_data = []

    with ThreadPoolExecutor(max_workers=INSTANCES) as executor:
        futures = [executor.submit(process_board, segment) for segment in segments]

        for future in as_completed(futures):
            all_data.extend(future.result())

    # Print or save the aggregated data
    with open('aggregated_data.json', 'w') as f:
        json.dump(all_data, f, indent=4)

    print(f"Processing complete. Data saved to 'aggregated_data.json'. Len data: {len(all_data)}")
