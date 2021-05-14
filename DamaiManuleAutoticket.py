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
target_url = 'https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.1d9b6a63WSaGQw&id=643803994352&clicktitle=%E5%BE%B7%E4%BA%91%E7%A4%BE%E7%9B%B8%E5%A3%B0%E5%A4%A7%E4%BC%9A%E2%80%94%E2%80%94%E5%A4%A9%E6%B4%A5%E5%BE%B7%E4%BA%91%E7%A4%BE'
name = ""
phone = ""
target_price = [5, 4, 3, 2, 1]
target_session = [1]
target_date = 9


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
        if self.status == 2:  # 登录成功入口
            self.num = 1  # 第一次尝试

            while self.driver.title.find('确认订单') == -1:  # 如果跳转到了订单结算界面就算这步成功了，否则继续执行此步
                # print(self.driver.title)
                # try:各种按钮的点击,
                try:
                    buybutton = self.driver.find_element_by_class_name('buybtn').text
                    if buybutton == "即将开抢":
                        self.status = 2
                        self.driver.get(target_url)
                        print('###抢票未开始，刷新等待开始###')
                        continue
                    elif buybutton == "立即预定":
                        self.choose_date()
                        self.driver.find_element_by_class_name('buybtn').click()
                        self.status = 3
                        self.num = 1
                    elif buybutton == "立即购买":
                        self.choose_date()
                        self.driver.find_element_by_class_name('buybtn').click()
                        self.status = 4
                    # 选座购买暂时无法完成自动化
                    elif buybutton == "选座购买":
                        self.choose_date()
                        self.status = 5
                        self.driver.find_element_by_class_name('buybtn').click()
                        print("自助选票")
                        break
                    elif buybutton == "提交缺货登记":
                        print("="*30)
                        print("###GG,没票了###")
                except Exception as e:
                    print(e, '###未跳转到订单结算界面###')

                # if title !="确认订单" : #如果前一次失败了，那就刷新界面重新开始
                #     self.status=2
                #     self.driver.get(target_url)
                #     print('###抢票失败，从新开始抢票###')
            print("###日期和票价选择成功###")

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
                (By.CSS_SELECTOR, 'body > div.perform > div.w1200.box.flex > div.flex1 > div.hd > div > div.order '
                                  '> div.perform__order__box > div:nth-child(7) > div.select_right')))
        # price = self.driver.find_element_by_id('priceList')

        price_list = price.find_element_by_class_name('select_right_list').find_elements_by_class_name(
            'select_right_list_item')

        print('可选票档数量为：{}'.format(len(price_list)))
        for i in target_price:
            print("选择第", i, "档")
            j = price_list[i - 1]
            try:
                j.click()
                break
            except Exception as e:
                print(e, "无法点击")
                continue

    def choice_seats(self):

        print("---------------", self.driver.title)
        try:
            while self.driver.title == '选座购买':
                while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[1]/div[2]/img'):
                    print('请快速的选择您的座位！！！')
                while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[2]/div'):
                    self.driver.find_element_by_xpath('//*[@id="app"]/div[2]/div[2]/div[2]/button').click()

            self.status = 3
        except Exception as e:
            print(e)

        # self.check_order()

        # submit_btn = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
        #     EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/button')))
        # submit_btn.click()

    def check_order(self):

        if self.status in [5]:
            print("###开始自行选座###")
            self.choice_seats()

        if self.status in [3, 4]:
            print('###开始确认订单###')

            try:
                # 默认选第一个购票人信息
                self.driver.find_element_by_xpath(
                    '//*[@id="confirmOrder_1"]/div[2]/div[2]/div[1]/div[1]/label/span[1]').click()

            except Exception as e:
                print("###购票人信息选中失败，自行查看元素位置###")
                print(e)

            # 最后一步提交订单

            time.sleep(0.5)  # 太快会影响加载，导致按钮点击无效
            self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[2]//div//div[9]//button[1]')[0].click()

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
# 手慢了，您选择的座位已被抢占，请重新选择

if __name__ == '__main__':
    con = Concert()  # 具体如果填写请查看类中的初始化函数
    # while True:
    # try:
    con.enter_concert()
    con.choose_ticket()
    con.check_order()
    # break
    # except Exception as e:
    #     print("抢票失败 重试", e)
    #     con.driver.get(target_url)

    # con.finish()
