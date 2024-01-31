import csv
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_page_content_selenium(url):
    options = webdriver.FirefoxOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver


def choose_page(driver, page_number, upper_lower="page"):
    try:
        page_selector = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, f'//span[@aria-label="{upper_lower} {page_number}"]')
            )
        )
        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "explore__link"))
        )
        print(f"Page {page_number} is ready")
        page_selector.click()
        return driver
    except Exception as e:
        print(f"Failed to select page {page_number}. Error: {e}")


def get_hero_links(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "explore__link"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        container = soup.find("div", class_="full-content")
        if container:
            characters_list = container.find_all("div", class_="mvl-card--explore")
            return [character.find("a")["href"] for character in characters_list]
    except Exception as e:
        print(f"Failed to wait for hero links. Error: {e}")
    return None


def get_page_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            return soup
        else:
            print(
                f"Failed to retrieve page content. Status code: {response.status_code}"
            )
    except Exception as e:
        print(f"An error occurred: {e}")
    return None


def parse_marvel_characters(character_links):
    characters_data = []
    labels = [
        "Universe",
        "Other Aliases",
        "Education",
        "Place of Origin",
        "Identity",
        "Known Relatives",
    ]

    for url in character_links:
        soup = get_page_content(f"https://www.marvel.com{url}")

        if not soup:
            continue

        result_data = {
            "Name": "N/A",
            "Link": f"https://www.marvel.com{url}",
        }

        name_element = soup.find("span", {"class": "masthead__headline"})
        if name_element:
            result_data["Name"] = name_element.text.strip()

        for label in labels:
            item = soup.find("p", {"class": "railBioInfoItem__label"}, string=label)
            if item:
                values = [
                    li.text.strip()
                    for li in item.find_next("ul", {"class": "railBioLinks"}).find_all(
                        "li"
                    )
                ]
                result_data[label] = values

        characters_data.append(result_data)

    return characters_data


def save_to_csv(data, filename):
    fieldnames = [
        "Name",
        "Link",
        "Universe",
        "Other Aliases",
        "Education",
        "Place of Origin",
        "Identity",
        "Known Relatives",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def get_total_pages(driver):
    if driver.page_source:
        soup = BeautifulSoup(driver.page_source, "html.parser")

        pagination = soup.find("ul", class_="pagination")

        if pagination:
            page_items = pagination.find_all("li", class_="pagination__item")

            last_page_text = page_items[-2].find("span").text

            if last_page_text.isdigit():
                total_pages = int(last_page_text)
                return total_pages

    return 1


if __name__ == "__main__":
    marvel_url = "https://www.marvel.com/characters"
    driver = get_page_content_selenium(marvel_url)
    hero_data = []

    for page in range(2, get_total_pages(driver)):
        driver = choose_page(driver, page)
        hero_links = get_hero_links(driver)
        if hero_links:
            hero_data.extend(hero_links)

    driver = choose_page(driver, 78, "Page")
    hero_data.extend(get_hero_links(driver))

    characters_data = parse_marvel_characters(hero_data)
    save_to_csv(characters_data, "marvel_characters.csv")

    driver.quit()
