from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

chrome_path = "./chromedriver.exe"
profile_path = "./selenium"

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={profile_path}")
root = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)

root.get('https://www.epicgames.com/store/en-US/free-games')

div_discover_xpath = '//*[@id="dieselReactWrapper"]/div/div[4]/main/div/div/div/div/div[2]/div[2]/div/div/section/div/*'
text_button_xpath = './/div/div/a/div/div/div[1]/div[2]/div/div/span'
link_xpath = './/div/div/a'

games = root.find_elements_by_xpath(div_discover_xpath)
links = []

for game in games:
    button = game.find_element_by_xpath(text_button_xpath)
    if button.text.upper() == 'FREE NOW':
        link = game.find_element_by_xpath(link_xpath)
        link = link.get_attribute('href')
        links.append(link)

overlay_xpath = '//*[@id="dieselReactWrapper"]/div/div[4]/main/div[2]/div/div[2]/div/button'
get_button_xpath = '/html/body/div[1]/div/div[4]/main/div/div/div[2]/div/div[2]/div[2]/div/div/div[3]/div/div/div/div[3]/div/div/button'
confirm_button_xpath = '//*[@id="purchase-app"]/div/div[4]/div[1]/div[2]/div[6]/div[2]/div/div[2]/button[2]'


def place_order():
    place_order_button = WebDriverWait(root, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-primary')))
    place_order_button.click()
    confirm_button = WebDriverWait(root, 10).until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
    confirm_button.click()
    sleep(5)


for link in links:
    root.get(link)
    main_div = root.find_elements_by_xpath('//main/*')
    for i in range(1, len(main_div)):
        root.execute_script(f"""
            var element = document.querySelector("main").children[{i}];
            if (element)
                element.parentNode.removeChild(element)
        """)
    try:
        main_button = WebDriverWait(root, 10).until(EC.presence_of_element_located((By.XPATH, get_button_xpath)))
        button_text = main_button.find_element_by_xpath('.//span').text.lower()
        if button_text == 'owned':
            continue
        elif button_text == 'get':
            main_button.click()
            place_order()
    except TimeoutException:
        get_buttons = root.find_elements_by_tag_name('button')
        for i, button in enumerate(get_buttons):
            try:
                if button.find_element_by_xpath('.//span').text.lower() == 'get':
                    button.click()
                    place_order()
                    if i < len(get_buttons) - 1:
                        links.append(link)
            except NoSuchElementException:
                continue

root.close()
