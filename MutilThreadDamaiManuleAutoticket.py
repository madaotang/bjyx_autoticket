import _thread
import os
import re
import time
import pickle
from tkinter import *
from time import sleep
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC, wait, expected_conditions
from selenium.webdriver.common.action_chains import ActionChains

# 大麦网主页
damai_url = "https://www.damai.cn/"
# 登录页
login_url = "https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F"
# 抢票目标页
target_url = 'https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.267a4d156bKiHo&id=644672951150&clicktitle=%E5%BC%80%E5%BF%83%E9%BA%BB%E8%8A%B12021%E5%B9%B4%E4%B8%AD%E5%A4%A7%E6%88%8F%E3%80%8A%E5%8F%8C%E5%9F%8E%E7%8E%AF%E6%A2%A6%E8%AE%B0%E3%80%8B'
name = ""
phone = ""
target_price = 2
target_session = [2]
target_date = 0
target_title = '开心麻花'


class Concert(object):
    def __init__(self):
        self.status = 0  # 状态,表示如今进行到何种程度
        self.login_method = 1  # {0:模拟登录,1:Cookie登录}自行选择登录方式
        self.total_wait_time = 3  # 页面元素加载总等待时间
        self.refresh_wait_time = 0.3  # 页面元素等待刷新时间
        self.intersect_wait_time = 0.5  # 间隔等待时间，防止速度过快导致问题

    def set_cookie(self):
        self.driver.get(damai_url)
        print("###请点击登录###")
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:
            sleep(1)
        print('###请扫码登录###')

        while self.driver.title != '大麦网-全球演出赛事官方购票平台-100%正品、先付先抢、在线选座！':
            sleep(1)
        print("###扫码成功###")
        pickle.dump(self.driver.get_cookies(), open("damai_cookies.pkl", "wb"))
        print("###Cookie保存成功###")
        self.driver.get(target_url)

    def get_cookie(self):
        try:
            cookies = pickle.load(open("damai_cookies.pkl", "rb"))  # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.damai.cn',  # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print('###载入Cookie###')
        except Exception as e:
            print(e)

    def login(self):
        if self.login_method == 0:
            self.driver.get(login_url)  # 载入登录界面
            print('###开始登录###')

        elif self.login_method == 1:
            if not os.path.exists('damai_cookies.pkl'):  # 如果不存在cookie.pkl,就获取一下
                self.set_cookie()
            else:
                self.driver.get(target_url)
                self.get_cookie()

    def enter_concert(self):
        print('###打开浏览器，进入大麦网###')
        self.driver = webdriver.Chrome(
            executable_path='chromedriver.exe')  # 默认Chrome浏览器
        # self.driver.maximize_window()           #最大化窗口
        self.login()  # 先登录再说
        self.driver.refresh()  # 刷新页面
        self.status = 2  # 登录成功标识
        print("###登录成功###")

    def dismiss_popup(self):
        # realname-popup-wrap realname-popup
        print("##点击知道了##")

        pop_up = self.driver.find_element(By.CLASS_NAME, "realname-popup")
        while pop_up.is_displayed():
            pop_up.find_element_by_xpath('/html/body/div[2]/div[2]/div/div/div[3]/div[2]').click()

    def choose_ticket(self):
        while True:
            if self.driver.title.find(target_title) != -1:
                # print(self.driver.title)
                # try:各种按钮的点击,
                try:
                    buybutton = self.driver.find_element_by_class_name('buybtn').text
                    if buybutton == "即将开抢":
                        self.status = 2
                        self.driver.get(target_url)
                        print('###抢票未开始，刷新等待开始###')
                        continue
                    elif buybutton == "选座购买":
                        self.choose_date()
                        self.status = 5
                        self.driver.find_element_by_class_name('buybtn').click()
                        print("自助选票")
                    else:
                        print("=" * 30)
                        print("###GG,没票了###")
                except Exception as e:
                    print(e, '###未跳转到订单结算界面###')

                # if title !="确认订单" : #如果前一次失败了，那就刷新界面重新开始
                #     self.status=2
                #     self.driver.get(target_url)
                #     print('###抢票失败，从新开始抢票###')
                print("###日期和票价选择成功###")
            else:
                time.sleep(0.2)

    def choose_date(self):
        print("=" * 30)
        print("###消除弹窗###")
        # self.dismiss_popup()
        print("###开始进行日期及票价选择###")
        if target_date != 0:  # 如果需要选择日期
            calendar = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.presence_of_element_located((By.CLASS_NAME, "functional-calendar")))
            datelist = calendar.find_elements_by_css_selector("[class='wh_content_item']")  # 找到能选择的日期
            datelist = datelist[7:]  # 跳过前面7个表示周一~周日的元素

            datelist[target_date - 1].click()  # 选择对应日期

        selects = self.driver.find_elements_by_class_name('perform__order__select')
        print('可选区域数量为：{}'.format(len(selects)))
        for item in selects:
            if item.find_element_by_class_name('select_left').text == '场次':
                session = item
                # print('\t场次定位成功')
            elif item.find_element_by_class_name('select_left').text == '票档':
                price = item
                # print('\t票档定位成功')

        session_list = session.find_elements_by_class_name('select_right_list_item')
        print('可选场次数量为：{}'.format(len(session_list)))
        if len(target_session) == 1:
            j = session_list[target_session[0] - 1].click()
        else:
            for i in target_session:  # 根据优先级选择一个可行场次
                j = session_list[i - 1]
                k = self.isClassPresent(j, 'presell', True)
                if k:  # 如果找到了带presell的类
                    if k.text == '无票':
                        continue
                    elif k.text == '预售':
                        j.click()
                        break
                else:
                    j.click()
                    break

        sleep(self.intersect_wait_time)

        price = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div/div[1]/div[1]/div/div[2]/div[3]/div[5]/div[2]/div')))
        # price = self.driver.find_element_by_id('priceList')

        price_list = price.find_elements_by_class_name(
            'select_right_list_item')

        print('可选票档数量为：{}'.format(len(price_list)))
        price_list[len(price_list) - target_price].click()

    def finish(self):
        self.driver.quit()

    def isElementExist(self, element):
        flag = True
        browser = self.driver
        try:
            browser.find_element_by_xpath(element)
            return flag

        except:
            flag = False
            return flag

    def check(self):
        while True:
            if self.driver.title == '确认订单':
                print('###开始确认订单###')

                time.sleep(0.3)  # 太快会影响加载，导致按钮点击无效
                # self.driver.find_elements_by_xpath('//*[@id="confirmOrder_1"]/div[8]/button')[0].click()
            else:
                sleep(0.2)

    def monitor_seats_choose(self):
        while True:
            if self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[2]/div'):
                self.driver.find_element_by_xpath('//*[@id="app"]/div[2]/div[2]/div[2]/button').click()
            else:
                sleep(0.2)

    def start(self):
        self.enter_concert()
        try:
            _thread.start_new_thread(con.choose_ticket, ())
            _thread.start_new_thread(con.monitor_seats_choose, ())
            _thread.start_new_thread(con.check, ())

        except:
            print("Error: 无法启动线程")

        while 1:
            pass


# 手慢了，您选择的座位已被抢占，请重新选择

if __name__ == '__main__':
    con = Concert()  # 具体如果填写请查看类中的初始化函
    con.start()
