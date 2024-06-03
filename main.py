import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from UnituDriver import UnituDriver


def process_board(urls):
    driver = UnituDriver(headless=HEADLESS)
    driver.login()

    for idx, url in enumerate(urls, start=1):
        driver.grab_active_posts(url)
        driver.grab_archived_posts(url)

    return driver.collect_data()


INSTANCES = 5
HEADLESS = True

if __name__ == '__main__':
    driver = UnituDriver(headless=HEADLESS)
    driver.login()

    urls = driver.get_all_board_urls()

    # Divide the URLs into INSTANCES segments
    segments = [urls[i::INSTANCES] for i in range(INSTANCES)]

    all_data = []

    with ThreadPoolExecutor(max_workers=INSTANCES) as executor:
        futures = [executor.submit(process_board, segment) for segment in segments]

        for future in as_completed(futures):
            all_data.extend(future.result())

    # Print or save the aggregated data
    with open('aggregated_data.json', 'w') as f:
        json.dump(all_data, f, indent=4)

    print(f"Processing complete. Data saved to 'aggregated_data.json'. Len data: {len(all_data)}")
