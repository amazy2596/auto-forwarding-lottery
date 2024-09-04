from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from pywinauto import Application
from selenium import webdriver
from dotenv import load_dotenv
from dotenv import set_key
import sqlite3
import json
import time
import re
import os

pattern = r'(?:(\d{4})[年\-\.\/\\])?\s*(\d{1,2})\s*[月\-\.\/\\]\s*(\d{1,2})\s*[日号]?'

def open_browser():

    options = Options()
    options.add_argument("--start-maximized")  # 启动时最大化窗口
    # options.add_argument("--headless")  # 启用无界面模式

    service = Service(os.getenv("driver_path"))
    
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def get_cookies(driver):
    
    driver.get("https://www.bilibili.com")
    
    input("请登录后按回车键继续...")
    
    cookies = driver.get_cookies()
    
    with open('cookies.json', 'w') as f:
        json.dump(cookies, f)
    
    
def load_cookies_from_env():
    
    with open('cookies.json', 'r') as f:
        return json.load(f)

def log_in(driver):

    driver.get("https://www.bilibili.com")
    
    max_retries = 5
    retry_count = 0
    
    cookies = load_cookies_from_env()
    
    time.sleep(3)
    
    while retry_count < max_retries:
        
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        driver.refresh()
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "header-avatar-wrap")))
            print("登录成功")
            return True
        except Exception as e:
            retry_count += 1
            print(f"登录失败: {e}")
            print(f"重试第 {retry_count} 次...")
            time.sleep(3)

    print("登录多次失败，退出程序")
    return False

def comment_and_forward(driver, dynamic, name, content):
    
    WebDriverWait(dynamic, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "bili-dyn-action"))
    )
    
    comment_icon = dynamic.find_elements(By.CLASS_NAME, "bili-dyn-action")[1]
    
    ActionChains(driver)\
        .click(comment_icon)\
        .pause(1)\
        .perform()
    
    input_box = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "reply-box-textarea"))
    )
    
    ActionChains(driver)\
        .click(input_box)\
        .pause(1)\
        .perform()
    
    forward_button = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "forward-input"))
    )
    
    ActionChains(driver)\
        .click(forward_button)\
        .pause(1)\
        .click(input_box)\
        .perform()
    
    submit_button = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "send-text"))
    )
    
    ActionChains(driver)\
        .send_keys(content + "@" + name)\
        .pause(1)\
        .click(submit_button)\
        .pause(1)\
        .click(comment_icon)\
        .perform()

def get_up_dynamic(driver, name):
    
    time.sleep(1)
    
    driver.refresh()
    
    dynamic_icon = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "n-dynamic"))
    )
    
    ActionChains(driver)\
        .click(dynamic_icon)\
        .perform()\
            
    WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "bili-dyn-list__items"))
    )
    
    dynamics = driver.find_elements(By.CLASS_NAME, "bili-dyn-list__item")
    count = 0
    
    while len(dynamics) < 100 and count < 30:
        ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
        dynamics = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bili-dyn-list__items"))
        ).find_elements(By.CLASS_NAME, "bili-dyn-list__item")
        time.sleep(0.1)
        count += 1
        
    dynamics = driver.find_elements(By.CLASS_NAME, "bili-dyn-list__item")
    
    for dynamic in dynamics:
        
        try:
            more = dynamic.find_element(By.CLASS_NAME, "bili-rich-text__action")
            
            if more.text == "展开":
                ActionChains(driver)\
                    .click(more)\
                    .perform()\
            
        except NoSuchElementException:
            pass

        try:

            content = dynamic.find_element(By.CLASS_NAME, "reference").text
            
            print("转发的动态")
            
            if "抽奖" in dynamic.text:
            
                try:
                    lottery = WebDriverWait(dynamic, 1).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "lottery"))
                    )
                    
                    ActionChains(driver).click(lottery).perform()
                    
                    try:
                        iframe_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__content__browser"))
                        )
                        
                        driver.switch_to.frame(iframe_element)
                        
                        open_time = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "lottery--incomplete"))
                        )
                        
                        open_time = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', open_time.text).group()
                        
                        open_time = datetime.strptime(open_time, "%Y年%m月%d日")
                        
                        join_icon = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "join-button"))
                        )
                        
                        ActionChains(driver).click(join_icon).pause(1).perform()
                        
                        driver.switch_to.default_content()
                        
                        esc_icon = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__header__close"))
                        )
                        
                        ActionChains(driver).click(esc_icon).perform()
                        
                        name = dynamic.find_element(By.CLASS_NAME, "dyn-orig-author__name").text
                        
                        if open_time > datetime.now() - timedelta(days=1) and check(datetime.strftime(open_time, "%Y-%m-%d"), name, content):
                            store(datetime.strftime(open_time, "%Y-%m-%d"), name, content)
                        
                    except (NoSuchElementException, TimeoutException):
                        
                        driver.switch_to.default_content()
                        
                        esc_icon = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__header__close"))
                        )
                        
                        ActionChains(driver).click(esc_icon).perform()

                except (NoSuchElementException, TimeoutException):
                    pass
            
        except NoSuchElementException:
            
            try:
            
                content = dynamic.find_element(By.CLASS_NAME, "bili-dyn-content").text

                if "抽奖" in content:
            
                    post_time = dynamic.find_element(By.CLASS_NAME, "bili-dyn-time").text
                    
                    post_time = post_time.split(' ')[0]
                    
                    if '年' in post_time:
                        post_time = datetime.strptime(post_time, "%Y年%m月%d日")
                    elif '月' in post_time and '日' in post_time:
                        post_time = str(datetime.now().year) + '年' + post_time
                        post_time = datetime.strptime(post_time, "%Y年%m月%d日")
                    elif '天前' in post_time:
                        num = re.search(r'\d+', post_time).group()
                        post_time = datetime.now() - timedelta(days=int(num))
                    elif '昨天' in post_time:
                        post_time = datetime.now() - timedelta(days=1)
                    elif '小时前' in post_time:
                        post_time = datetime.now() - timedelta(hours=int(re.search(r'\d+', post_time).group()))
                    elif '分钟前' in post_time:
                        post_time = datetime.now() - timedelta(minutes=int(re.search(r'\d+', post_time).group()))
                    elif '直播' in post_time:
                        continue
                    
                    if post_time < datetime.now() - timedelta(days=180):
                        continue
                    
                    open_time = None    
                    
                    try:
                        
                        lottery = WebDriverWait(dynamic, 1).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "lottery"))
                        )
                        
                        try:
                    
                            follow_icon = WebDriverWait(driver, 1).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "h-follow"))
                            )
                    
                            ActionChains(driver)\
                                .click(follow_icon)\
                                .perform()\
                            
                        except (NoSuchElementException, TimeoutException):
                            pass
                        
                        ActionChains(driver).click(lottery).perform()
                        
                        try:
                            iframe_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__content__browser"))
                            )
                            
                            driver.switch_to.frame(iframe_element)
                            
                            open_time = WebDriverWait(driver, 1).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "lottery--incomplete"))
                            )
                            
                            open_time = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', open_time.text).group()
                            
                            open_time = datetime.strptime(open_time, "%Y年%m月%d日")
                            
                            join_icon = WebDriverWait(driver, 1).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "join-button"))
                            )
                            
                            ActionChains(driver).click(join_icon).pause(1).perform()
                            
                            driver.switch_to.default_content()
                            
                            esc_icon = WebDriverWait(driver, 1).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__header__close"))
                            )
                            
                            ActionChains(driver).click(esc_icon).perform()
                            
                            if open_time > datetime.now() - timedelta(days=1) and check(datetime.strftime(open_time, "%Y-%m-%d"), name, content):
                                store(datetime.strftime(open_time, "%Y-%m-%d"), name, content)
                            
                        except (NoSuchElementException, TimeoutException):
                            
                            driver.switch_to.default_content()
                            
                            esc_icon = WebDriverWait(driver, 1).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "bili-popup__header__close"))
                            )
                            
                            ActionChains(driver).click(esc_icon).perform()

                    except (NoSuchElementException, TimeoutException):
                                
                        try:
                            
                            year, month, day = re.search(pattern, content, re.VERBOSE).groups()
                        
                            if not year:
                                year = datetime.now().year
                                
                            date_str = f"{year}-{int(month):02}-{int(day):02}"
                                
                            try:
                                open_time = datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                print(f"日期格式解析错误: {date_str}")
                            
                            if post_time > datetime.now() - timedelta(days=180) and (open_time is not None) and open_time - timedelta(days=1) > datetime.now() and check(datetime.strftime(open_time, "%Y-%m-%d"), name, content):
                                
                                try:
                            
                                    follow_icon = WebDriverWait(driver, 1).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "h-follow"))
                                    )
                            
                                    ActionChains(driver)\
                                        .click(follow_icon)\
                                        .perform()\
                                    
                                except (NoSuchElementException, TimeoutException):
                                    pass
                                
                                comment_and_forward(driver, dynamic, name, content)
                                
                                store(datetime.strftime(open_time, "%Y-%m-%d"), name, content)
                                
                        except (AttributeError, ValueError):
                            pass
            except NoSuchElementException:
                pass

def random_search_up(driver):
    
    while True:
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "feed-card"))
        )
        
        roll_icon = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "roll-btn"))
        )
        
        up_cards = driver.find_elements(By.CLASS_NAME, "feed-card")
        
        for up_card in up_cards:
            
            name_icon = up_card.find_element(By.CLASS_NAME, "bili-video-card__info--author")
            name = name_icon.text
            
            try:
                
                ad_element = up_card.find_element(By.CLASS_NAME, "bili-video-card__info--ad")
                
                if ad_element is not None:
                    continue
                    
            except NoSuchElementException:
                
                ActionChains(driver)\
                .click(name_icon)\
                .pause(1)\
                .perform()\
                    
                original_window = driver.current_window_handle
                windows = driver.window_handles
                
                for window in windows:
                    if window != driver.current_window_handle:
                        driver.switch_to.window(window)
                        break
                
                get_up_dynamic(driver, name)
                
                for window in windows:
                    if window != original_window:
                        driver.close()
                        driver.switch_to.window(original_window)
                        break
                    
                time.sleep(10)
                
        ActionChains(driver)\
            .click(roll_icon)\
            .perform()\
                
        time.sleep(1)
        
def subject_of_lottery(driver):
    
    urls = [
        "https://www.bilibili.com/v/topic/detail/?topic_id=1094880&topic_name=%E5%8A%A8%E6%80%81%E4%BA%92%E5%8A%A8%E6%8A%BD%E5%A5%96&spm_id_from=333.999.list.card_topic.click",
        "https://www.bilibili.com/v/topic/detail/?topic_id=1182230&topic_name=%E6%8A%BD%E5%A5%96%23%20%23%E8%BD%AC%E5%8F%91%E6%8A%BD%E5%A5%96%23%20%23%E4%BA%92%E5%8A%A8%20%E6%8A%BD%E5%A5%96&spm_id_from=333.1369.opus.module_topic.click"
    ]
    
    for url in urls:
        
        driver.get(url)
        
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bili-dyn-item"))
        )
        
        dynamics = driver.find_elements(By.CLASS_NAME, "bili-dyn-item__main")
        count = 0
        
        while len(dynamics) < 100 and count < 30:
            ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
            dynamics = driver.find_elements(By.CLASS_NAME, "bili-dyn-item__main")
            time.sleep(0.1)
            count += 1
            
        dynamics = driver.find_elements(By.CLASS_NAME, "bili-dyn-item__main")
        
        for dynamic in dynamics:    
            
            name = dynamic.find_element(By.CLASS_NAME, "bili-dyn-title").text
            
            try:
                more = dynamic.find_element(By.CLASS_NAME, "bili-rich-text__action")
                
                if more.text == "展开":
                    ActionChains(driver).click(more).perform()
                    
            except NoSuchElementException:
                pass
                
            content = dynamic.find_element(By.CLASS_NAME, "bili-dyn-content").text
                
            try:
                
                year, month, day = re.search(pattern, content, re.VERBOSE).groups()
                
                if not year:
                    year = datetime.now().year
                    
                date_str = f"{year}-{int(month):02}-{int(day):02}"
                    
                try:
                    open_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    print(f"日期格式解析错误: {date_str}")
                
                if open_date > datetime.now() - timedelta(days=1) and check(datetime.strftime(open_date, "%Y-%m-%d"), name, content):
                    
                    try:
                        
                        follow_icon = dynamic.find_element(By.CLASS_NAME, "bili-dyn-follow-btn")
                        
                        if follow_icon.text == "关注":
                            ActionChains(driver).click(follow_icon).perform()
                        
                    except NoSuchElementException:
                        pass
                    
                    comment_and_forward(driver, dynamic, name, content)
                        
                    store(datetime.strftime(open_date, "%Y-%m-%d"), name, content)
                
            except (AttributeError, ValueError):
                pass
        
def search_following_up(driver):
    url = "https://space.bilibili.com/3546745956993982/fans/follow?spm_id_from=333.1007.0.0"
    driver.get(url)
    
    time.sleep(3)
    
    num = 0
    total = driver.find_element(By.CLASS_NAME, "be-pager-total").text
    total = int(re.search(r'\d+', total).group())
    
    while num < total:
            
        next_page = driver.find_element(By.CLASS_NAME, "be-pager-next")
        
        name_buttons = driver.find_elements(By.CLASS_NAME, "fans-name")
        
        for name_button in name_buttons:
            
            name = name_button.text
            
            ActionChains(driver).click(name_button).perform()
            
            original_window = driver.current_window_handle
            windows = driver.window_handles
            
            for window in windows:
                if window != driver.current_window_handle:
                    driver.switch_to.window(window)
                    break
            
            get_up_dynamic(driver, name)
            
            for window in windows:
                if window != original_window:
                    driver.close()
                    driver.switch_to.window(original_window)
                    break
                
            time.sleep(10)
            
        ActionChains(driver).click(next_page).perform()
        
        time.sleep(1)
        
        num += 1
        
def open_database():
    
    current_dir = os.path.dirname(__file__)
    database_path = os.path.join(current_dir, 'added.db')
    
    global conn, cursor
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events(
            time TEXT,
            name TEXT,
            content TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opened(
            time TEXT,
            name TEXT,
            content TEXT
        )
    ''')
    
    conn.commit()

def check(time, name, content):
    queries = [
        "select * from events where content = ?",
        "select * from opened where content = ?",
        "select * from events where time = ? and name = ?",
        "select * from opened where time = ? and name = ?"
    ]
    
    parameters = [
        (content,),
        (content,),
        (time, name),
        (time, name)
    ]
    
    for query, param in zip(queries, parameters):
        cursor.execute(query, param)
        result = cursor.fetchall()
        if result:
            return False
    
    return True
        
def store(date, name, content):
    cursor.execute(f"insert into events (time, name, content) values(?, ?, ?)", (date, name, content))
    print(f"存储: {date} {name} {content}")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM events")
    row_count = cursor.fetchone()[0]
    print(f"插入后的总行数: {row_count}")
    
    time.sleep(300)
        
def remove_old_entries():
    current_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    cursor.execute("insert into opened select * from events where time < ?", (current_time, ))
    cursor.execute("delete from events where time < ?", (current_time, ))
    conn.commit()
        
def fetch_and_sort_entries():
    cursor.execute("select * from events")
    entries = cursor.fetchall()
    sorted_entries = sorted(entries, key = lambda x : datetime.strptime(x[0], "%Y-%m-%d"))
    return sorted_entries

def clear_table():
    cursor.execute("delete from events")
    conn.commit()
    
def store_sorted_entries(sorted_entries):
    for entry in sorted_entries:
        cursor.execute("insert into events (time, name, content) values(?, ?, ?)", (entry[0], entry[1], entry[2]))
        conn.commit()

if __name__ == "__main__":
    
    load_dotenv()
    
    driver = open_browser()
    
    # get_cookies(driver)
    
    open_database()
    
    if log_in(driver) == False:
        print("登录失败")
        driver.quit()
        exit()
            
    remove_old_entries()
    sorted_entries = fetch_and_sort_entries()
    clear_table()
    store_sorted_entries(sorted_entries)
        
    choice = 1
    
    while choice != 0:
            
        print("0. 退出")
        print("1. 随机搜索UP主")
        print("2. 话题抽奖")
        print("3. 搜索关注的UP主")
        
        choice = int(input("请输入选项: "))
        
        if choice == 0:
            break
        elif choice == 1:
            random_search_up(driver)
        elif choice == 2:
            subject_of_lottery(driver)
        elif choice == 3:
            search_following_up(driver)
        else:
            print("无效选项")
            
    cursor.close()
    conn.close()
    driver.quit()