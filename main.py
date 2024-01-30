import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Функція для отримання вмісту сторінки за допомогою Selenium
def get_page_content_selenium(url):
    options = webdriver.FirefoxOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get(url)
    return driver


def choose_page(driver, page_number, upper_lower="page"):
    try:
        # Очікуємо, щоб елемент став видимим на сторінці
        page_selector = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f'//span[@aria-label="{upper_lower} {page_number}"]',
                )
            )
        )

        # Прокручуємо до елемента, щоб уникнути перекриття
        time.sleep(2)
        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )

        time.sleep(2)
        page_selector.click()

        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "explore__link"))
        )
        print(f"Page {page_number} is ready")

        return driver
    except Exception as e:
        print(f"Failed to select page {page_number}. Error: {e}")


def get_hero_links(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "explore__link"))
        )
    except Exception as e:
        print(f"Failed to wait for hero links. Error: {e}")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", class_="full-content")

    if container:
        characters_list = container.find_all("div", class_="mvl-card--explore")
        hero_links = [character.find("a")["href"] for character in characters_list]
        return hero_links

    return None


def parse_marvel_characters(url):
    content = get_page_content_selenium(f"https://www.marvel.com{url}")
    characters_data = []

    if content:
        soup = BeautifulSoup(content.page_source, "html.parser")
        characters_list = soup.find_all("div", class_="text")

        for character in characters_list:
            data = {}
            data["name"] = character.find("a").text.strip()
            data["link"] = character.find("a")["href"]
            data["universe"] = "Marvel Universe"

            # You can add more characteristics if available
            # For example, data['other_aliases'] = character.find('div', class_='aliases').text.strip()

            # Add hero data to the list
            characters_data.append(data)

    return characters_data


def get_total_pages(driver):
    if driver.page_source:
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Знайти елемент з пагінацією
        pagination = soup.find("ul", class_="pagination")

        if pagination:
            # Знайти всі сторінки
            page_items = pagination.find_all("li", class_="pagination__item")

            # Знайти текст останньої сторінки (перед "Next")
            last_page_text = page_items[-2].find("span").text

            # Перевірити, чи текст останньої сторінки - це число
            if last_page_text.isdigit():
                total_pages = int(last_page_text)
                return total_pages

    return 1


def has_duplicates(array):
    # Перевірка, чи розмір оригінального масиву не рівний розміру set
    return len(array) != len(set(array))


if __name__ == "__main__":
    marvel_url = "https://www.marvel.com/characters"
    driver = get_page_content_selenium(marvel_url)

    hero_data = set(get_hero_links(driver))
    # print(hero_data)

    for page in range(2, 5):
        driver = choose_page(driver, page)
        hero_links = set(get_hero_links(driver))

        if hero_links:
            hero_data.update(hero_links)
        else:
            print(f"No hero links found on page {page}")

    driver = choose_page(driver, 78, "Page")
    hero_data.update(get_hero_links(driver))

    if has_duplicates(hero_data):
        print("Масив має повторювані елементи.")
    else:
        print("Масив не має повторюваних елементів.")

    print(list(hero_data))
    print(len(hero_data))
    driver.quit()
