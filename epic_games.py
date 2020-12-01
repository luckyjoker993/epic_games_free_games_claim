import pickle
import sys
import os
import traceback

from itertools import repeat
from time import sleep
from concurrent.futures import ThreadPoolExecutor as Threads

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

try:
    from epic_games_settings import number_of_browsers as workers, save_cookies, hide_browsers
except Exception:
    print('No setting.py file detected, continuing with default settings.')
    workers = 1
    save_cookies = 1
    hide_browsers = True

debug = 0

chrome_path = "./chromedriver.exe"
try:
    path = os.path.join(sys._MEIPASS, chrome_path)
except Exception:
    path = chrome_path

div_discover_xpath = '//*[@id="dieselReactWrapper"]/div/div[4]/main/div/div/div/div/div[2]/div[2]/div/div/section/div/*'
text_button_xpath = './/div/div/a/div/div/div[1]/div[2]/div/div/span'
link_xpath = './/div/div/a'
name_xpath = './/div/div/a/div/div/div[3]/span[1]'

overlay_xpath = '//*[@id="dieselReactWrapper"]/div/div[4]/main/div[2]/div/div[2]/div/button'
get_button_xpath = '/html/body/div[1]/div/div[4]/main/div/div/div[2]/div/div[2]/div[2]/div/div/div[3]/div/div/div/div[3]/div/div/button'
confirm_button_xpath = '//*[@id="purchase-app"]/div/div[4]/div[1]/div[2]/div[6]/div[2]/div/div[2]/button[2]'


def users():
    users = []
    with open('login.txt', 'r') as file:
        while True:
            login = file.readline().strip()
            if not login:
                break
            password = file.readline().strip()
            users.append((login, password))
    return users


# def get_links():
#     options = Options()
#     if hide_browsers:
#         options.add_argument('--window-position=-2000,0')
#     root = webdriver.Chrome(executable_path=path, options=options)
#     root.get('https://www.epicgames.com/store/en-US/free-games')
#     WebDriverWait(root, 60).until(lambda wd: len(wd.find_elements_by_xpath(div_discover_xpath)) != 0)
#     games = root.find_elements_by_xpath(div_discover_xpath)
#     links = []
#     # get links of free games
#     for game in games:
#         button = game.find_element_by_xpath(text_button_xpath)
#         if button.text.upper() == 'FREE NOW':
#             name = game.find_element_by_xpath(name_xpath).text
#             print(f'{name} is free now')
#             link = game.find_element_by_xpath(link_xpath)
#             link = link.get_attribute('href')
#             links.append((link, 0))
#     root.close()
#     return links


def get_links():
    options = Options()
    if hide_browsers:
        options.add_argument('--window-position=-2000,0')
    root = webdriver.Chrome(executable_path=path, options=options)
    root.get('https://www.epicgames.com/store/en-US/free-games')
    sleep(3)
    links = zip(set(root.execute_script('''
        window.scrollTo(0, document.body.scrollHeight);
        spans = document.getElementsByTagName('span');
        links = [];
        for (span of spans) {
            if(span.innerText.toLowerCase().includes('free now')){
                while(span.localName != 'a'){
                    span = span.parentElement;
                }
                links.push(span.href);
            }
        };
        return links;
        ''')), repeat(0))
    root.close()
    return links


def add_games(user, links):
    login, password = user
    options = Options()
    if hide_browsers:
        options.add_argument('--window-position=-2000,0')

    root = webdriver.Chrome(executable_path=path, options=options)

    # Load cookies
    try:
        with open(f'{user[0]}.pkl', 'rb') as file:
            cookies = pickle.load(file)
            root.get('https://www.epicgames.com/id/login')
            for cookie in cookies:
                root.add_cookie(cookie)
    except FileNotFoundError:
        print(f'{user[0]}:No cookies found')
        root.get('https://www.epicgames.com/id/login')

    # check if logged in
    sleep(3)
    if root.current_url != 'https://www.epicgames.com/account/personal':
        root.get('https://www.epicgames.com/id/login/epic')
        try:
            WebDriverWait(root, 15).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(login)
            root.find_element_by_id('password').send_keys(password)
            WebDriverWait(root, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'SubmitButton'))).click()
            if hide_browsers:
                root.set_window_position(0, 0)
        except TimeoutException:
            print(f'{login}: failed to login')
            return False
        while not root.current_url.startswith('https://www.epicgames.com/account/personal'):
            sleep(2)
        if hide_browsers:
            root.set_window_position(-2000, 0)

    # save cookies
    if save_cookies:
        with open(f'{user[0]}.pkl', 'wb') as cookies:
            pickle.dump(root.get_cookies(), cookies)
            print('saved cookies')

    # # accept cookies
    # try:
    #     cookies_button = WebDriverWait(root, 5).until(
    #         EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler')))
    #     root.execute_script('arguments[0].click()', cookies_button)
    # except TimeoutException:
    #     pass

    # loop through links
    for link, repeating in links:
        before = len(root.window_handles)
        root.execute_script('window.open()')
        while before == len(root.window_handles):
            pass
        root.switch_to.window(root.window_handles[-1])
        root.get(link)
        main_div = root.find_elements_by_xpath('//main/*')

        # remove overlays
        for i in range(1, len(main_div)):
            root.execute_script(f"""
                var element = document.querySelector("main").children[{i}];
                if (element)
                    element.parentNode.removeChild(element)
            """)

        # get 'GET' buttons from game page
        root.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(5)
        get_buttons = root.execute_script(
            """
                get_buttons = [];
                buttons = document.getElementsByTagName('button');
                for (button of buttons)
                    {if(button.innerText != undefined && button.innerText.toLowerCase().includes('get'))
                        {get_buttons.push(button)}};
                return get_buttons;
            """)

        # close if not get buttons
        if not get_buttons:
            if not repeating:
                print(f'{login}: {root.title} already in library')
            root.execute_script('window.close()')
            root.switch_to.window(root.window_handles[0])
            continue

        # if more than one get button add link to repeat
        if not repeating:
            [links.append((link, 1)) for _ in range(1, len(get_buttons))]

        # add game to library
        root.execute_script('arguments[0].click()', get_buttons[0])
        sleep(5)
        success = place_order(root, login)
        if success:
            if not repeating:
                print(f'{login}: {root.title} added to library')
            else:
                print(f'{login}: {root.title} DLC added to library')
            root.execute_script('window.close()')
            root.switch_to.window(root.window_handles[0])

    # close the user profile page
    root.switch_to.window(root.window_handles[0])
    root.close()
    try:
        if root.window_handles:
            if hide_browsers:
                root.set_window_position(0, 0)
        while root.window_handles:
            sleep(15)
    except:
        pass

    return


# function to handle confirming order
def place_order(root, login):
    tries = 5
    while tries:
        try:
            root.execute_script("document.getElementsByClassName('btn-primary')[0].click()")
            break

        except:
            tries -= 1
            if not tries:
                traceback.print_exc()
                print(f'{login}: something went wrong with {root.title}')
                return False
            sleep(5)

    # Confirm place order # removed
    # tries = 3
    # while tries:
    #     try:
    #         root.execute_script(
    #             "document.getElementsByClassName('overlay-modal-content')[0]\n"
    #             ".getElementsByClassName('btn-primary')[0].click()")
    #         break
    #     except:
    #         tries -= 1
    #         if not tries:
    #             traceback.print_exc()
    #             print(f'{login}: something went wrong with {root.title}')
    #             return False

    sleep(15)
    if '/verify?' in root.current_url:
        print(f'{login}: {root.title} needs to verify')
        if hide_browsers:
            root.set_window_position(0, 0)
        return False
    return True


def main():
    links = get_links()
    if debug:
        add_games(users()[0], links)
    else:
        with Threads(max_workers=workers) as executor:
            executor.map(add_games, users(), repeat(links))


if __name__ == "__main__":
    main()
