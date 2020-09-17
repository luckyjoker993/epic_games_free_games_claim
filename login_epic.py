from selenium import webdriver
from selenium.webdriver.chrome.options import Options


chrome_path = "./chromedriver.exe"
profile_path = "./selenium"

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={profile_path}")
root = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)

root.get('https://www.epicgames.com/id/login')