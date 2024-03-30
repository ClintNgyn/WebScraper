import re
from pathlib import Path
from datetime import datetime
from scraper import WebScraper
from scraper.exceptions import *


def main() -> bool:
    choice_dict = {
        "1": display_latest_deals,
        "2": analyze_deals_by_category,
        "3": find_top_stores,
        "4": log_deal_information,
        "5": quit_program,
    }

    # User input pages to scrape
    print("\n-> Welcome to my Web Scrapping Adventure App")
    try:
        max_pages = int(
            input("\n-> How many pages would you like to scrape (maximum 10): ")
        )
        assert 0 < max_pages <= 10
    except (ValueError, AssertionError):
        print("\n-> Invalid response. Scraping 2 pages (by default)")
        max_pages = 2

    # Prepare pages to scrape
    base_url = "https://forums.redflagdeals.com"
    paths = list()
    for i in range(1, max_pages + 1):
        paths.append(f"/hot-deals-f9/{i}")

    # Start Program
    try:
        scraper = WebScraper(base_url, *paths)
        while True:
            user_input = read_menu_option()
            choice_dict.get(user_input, invalid_choice)(scraper)

    except FetchError as f_ex:
        print(f"\n-> an HTTP error occurred")
        print(f"-> {f_ex}")
        print(f"-> Exiting...")
        exit(1)
    except Exception as e:
        print(f"\n-> an error occurred")
        print(f"-> {e}")
        print(f"-> Exiting...")
        exit(1)

    return True


def extract_store(deal) -> str:
    """Extract the store name from deal's html content"""

    # first format for retailer
    retailer = deal.select_one(".topictitle_retailer")
    if retailer:
        return retailer.text.strip()

    # possible second format for retailer
    retailer = deal.select_one(".topictitle")
    if retailer:
        match = re.search(
            r"\[(.*?)\]",
            retailer.text.strip(),  # extract name from inside "[ ]" brackets
        )
        if match:
            return match.group(1)

    # no retailer available
    return "n/a"


def display_latest_deals(scraper: WebScraper) -> None:
    """List the latest deals"""

    deals = list()
    soups = scraper.fetch_all()
    for soup in soups.values():
        deals += soup.select("ul.topics li.row.topic:not(.sticky)")

    print()
    print("-" * 100)
    print(f"{'***  Latest Deals  ***':^100}")
    print("-" * 100)

    for i, deal in enumerate(deals, start=1):
        # Extract deal information
        store = extract_store(deal)
        title = deal.select_one("a.topic_title_link")
        url = scraper.base_url + title["href"].strip() if title else "n/a"
        votes = deal.select_one(".total_count")
        username = deal.select_one(".thread_meta_author")
        category = deal.select_one(".thread_category a")
        timestamp = deal.select_one(".first-post-time")
        replies = deal.select_one(".posts")
        views = deal.select_one(".views")

        # Print formatted deal information
        deal_info = f"""
[Deal #{i}]
    Store: {store}
  Product: {title.text.strip() if title else 'n/a'}
    Votes: {votes.text.strip() if votes else 'n/a'}
 Username: {username.text.strip() if username else  'n/a'}
 Category: {category.text.strip() if category else  'n/a'}
Timestamp: {timestamp.text.strip() if timestamp else  'n/a'}
  Replies: {replies.text.strip() if replies else  'n/a'}
    Views: {views.text.strip() if views else  'n/a'}
      URL: {url}
"""
        print(deal_info)
        print("-" * 100)

    return None


def get_categories(deals: list) -> dict:
    """Count deals for each category"""

    categories_count = dict()
    for deal in deals:
        cat = deal.select_one(".thread_category a")
        if cat:
            cat_key = cat.text.strip()
            categories_count[cat_key] = categories_count.get(cat_key, 0) + 1

    return categories_count


def analyze_deals_by_category(scraper: WebScraper) -> None:
    """List categories base on the number of deals currently available in desc order"""
    deals = list()
    soups = scraper.fetch_all()
    for soup in soups.values():
        deals += soup.select("ul.topics li.row.topic:not(.sticky)")

    # Sort categories by number of deals
    categories_count = sorted(
        get_categories(deals).items(), key=lambda item: item[1], reverse=True
    )

    print()
    print("-" * 37)
    print(f"{'***  Deals by Category  ***':^37}")
    print("-" * 37)
    for cat, count in categories_count:
        print(f"{cat:>25}: {count:2} deals")
    print("-" * 37)

    return None


def find_top_stores(scraper: WebScraper) -> None:
    """List the top x stores where x is the number of stores to display, supplied by user"""

    deals = list()
    soups = scraper.fetch_all()
    for soup in soups.values():
        deals += soup.select("ul.topics li.row.topic:not(.sticky)")

    # Count deals for each store
    store_counts = dict()
    for deal in deals:
        store = extract_store(deal)
        if store != "n/a":
            store_counts[store] = store_counts.get(store, 0) + 1

    # Sort stores by deals
    store_counts = sorted(store_counts.items(), key=lambda item: item[1], reverse=True)

    # User input number of stores
    try:
        max_stores = int(input("How number of top stores to display: "))
        assert 0 <= max_stores <= len(store_counts)
    except (ValueError, AssertionError):
        max_stores = len(store_counts)
        print("\n-> Invalid response. Printing all stores...")

    print()
    print("-" * 42)
    print(f"{f'***  Top {max_stores} Stores  ***':^42}")
    print("-" * 42)
    for i, (k, v) in enumerate(store_counts[:max_stores], start=1):
        print(f"{f'[#{i}]':>5} {k:25} :{v:2} deals")
    print("-" * 42)

    return None


def log_deal_information(scraper: WebScraper) -> None:
    """Log deals of user specified category to file"""

    deals = list()
    soups = scraper.fetch_all()
    for soup in soups.values():
        deals += soup.select("ul.topics li.row.topic:not(.sticky)")

    print()
    print("-" * 37)
    print(f"{'***  List of Categories  ***':^37}")
    print("-" * 37)

    # Display categories
    categories = sorted(get_categories(deals).keys())
    for i, category in enumerate(categories, start=1):
        print(f"{f'[#{i}]':>5} {category}")
    print("-" * 37)

    # User selects a category
    try:
        user_cid = int(input("Enter category number you want to log: "))
        assert 1 <= user_cid <= len(categories)
        user_cat = categories[user_cid - 1]
    except (ValueError, AssertionError):
        print("\n-> Not a valid selection. Going back to main menu...")
        return

    # Prepare log files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_filename = f"{format_filename(user_cat)}-{timestamp}.log"
    log_directory = Path.cwd() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    # Log deals to file
    log_filepath = log_directory / log_filename
    try:
        with open(log_filepath, "a") as file:
            count = 1
            for deal in deals:
                title = deal.select_one("a.topic_title_link")
                category = deal.select_one(".thread_category a")

                if (
                    title
                    and category
                    and category.text.strip().lower() == user_cat.lower()
                ):
                    url = scraper.base_url + title["href"].strip()
                    file.write(f"[Deal #{count}] {title.text.strip()}:\n")
                    file.write(f"{url}\n")
                    file.write(f"\n")
                    count += 1
    except OSError as ose:
        print("\n-> File operation failed: {ose}")

    print(
        f'\n-> Successfully logged all links with category "[#{user_cid}] {user_cat}" as {log_filename}'
    )

    return None


def format_filename(str):
    return str.lower().replace(" ", "_").strip()


def quit_program(*args) -> None:
    print("\n-> Exiting. Thanks for using my Web Scrapping Adventure App")
    exit()


def invalid_choice(*args) -> None:
    # Notify the user of an invalid choice
    print("\n-> Invalid choice, please try again")
    return None


def read_menu_option() -> str:
    print(
        f"""
{'=' * 37}
{'*** Web Scrapping Adventure ***':^37}
{'=' * 37}
 1. Display Latest Deals
 2. Analyze Deals by Category
 3. Find Top Stores
 4. Log Deal Information
 5. QUIT
{'-' * 37}"""
    )

    return input("Enter your choice (1 to 5): ")


if __name__ == "__main__":
    main()
