from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from json import loads
from os.path import exists
from pickle import dump, load
from time import sleep, time


class Concert(object):
    def __init__(self, browser, target_url, date, ticket_num, receiver, viewer, target_price):
        self.viewer = viewer  # 观演人序号,目前还不能用,
        self.target_price = target_price
        self.receiver = receiver
        self.ticket_num = ticket_num
        self.date = date  # 日期选择
        self.status = 0
        self.target_url = target_url
        self.baoli_url = "https://www.polyt.cn/"
        self.browser = browser  # 0代表Chrome，1代表Firefox，默认为Chrome
        self.total_wait_time = 1000  # 页面元素加载总等待时间
        self.refresh_wait_time = 0.3  # 页面元素等待刷新时间
        self.intersect_wait_time = 0.5  # 间隔等待时间，防止速度过快导致问题
        self.time_start = 0  # 开始时间
        self.time_end = 0  # 结束时间
        self.num = 0  # 尝试次数

    def isClassPresent(self, item, name, ret=False):
        try:
            result = item.find_element_by_class_name(name)
            if ret:
                return result
            else:
                return True
        except:
            return False

    def get_cookie(self):
        self.driver.get(self.baoli_url)
        print("###请点击登录###")
        while self.driver.title.find('保利票务') == -1:  # 等待网页加载完成
            sleep(1)
        print("###请登录###")
        try:
            while self.driver.find_element_by_class_name('no-login').text == '登录/注册':  # 等待扫码完成
                sleep(1)
        except Exception as e:
            print("###登陆成功,开始保存cookie###")

        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        print("###Cookie保存成功###")

    def set_cookie(self):
        try:
            cookies = load(open("cookies.pkl", "rb"))  # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.polyt.cn',  # 必须有，不然就是假登录
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
        if not exists('cookies.pkl'):  # 如果不存在cookie.pkl,就获取一下
            if self.browser == 0:  # 选择了Chrome浏览器
                self.driver = webdriver.Chrome()
            elif self.browser == 1:  # 选择了Firefox浏览器
                self.driver = webdriver.Firefox()
            else:
                raise Exception("***错误：未知的浏览器类别***")
            self.get_cookie()
            self.driver.quit()
        print('###打开浏览器###')
        if self.browser == 0:  # 选择了Chrome浏览器，并成功加载cookie，设置不载入图片，提高刷新效率
            options = webdriver.ChromeOptions()
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(options=options)
        elif self.browser == 1:  # 选择了火狐浏览器
            options = webdriver.FirefoxProfile()
            options.set_preference('permissions.default.image', 2)
            self.driver = webdriver.Firefox(options)
        else:
            raise Exception("***错误：未知的浏览器类别***")
        self.driver.get(self.target_url)
        self.set_cookie()
        # self.driver.maximize_window()
        self.driver.refresh()

    def enter_concert(self):
        self.login()
        try:
            locator = (By.CLASS_NAME, 'has-login')
            WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.presence_of_element_located(locator))
            self.status = 1
            print("###登录成功###")
        except Exception as e:
            print(e)
            self.status = 0
            self.driver.quit()
            raise Exception("***错误：登录失败,请检查配置文件昵称或删除cookie.pkl后重试***")

    def choose_date(self):
        datepicker = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "choiceTime")))
        datelist = datepicker.find_elements_by_tag_name("span")

        for i, j in enumerate(self.date):

            try:
                # print("第", i, "次选座, 选择第", j, "日")
                datelist[j].click()

                buy_btn = self.driver.find_element_by_class_name('buy-btn')
                buy_btn.click()
                sleep(0.5)

            except Exception as e:
                print(e, "该天已不可选, 选择剩余日")

    def choose_price(self):
        prices = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "choicePrice")))
        prices_list = prices.find_elements_by_tag_name('button')

        for i in self.target_price:
            price = prices_list[i]
            if price.is_enabled():
                price.click()
                print("##成功选择第", i, "档票")
                return True

        return False

    def choose_ticket(self):
        self.time_start = time()
        print("###开始进行日期及票价选择###")

        while self.driver.title.find('选择座位') == -1:  # 如果跳转到了确认界面就算这步成功了，否则继续执行此步

            concert_status = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time) \
                .until(EC.presence_of_element_located((By.ID, 'sessionStatus')))

            if concert_status.text == "即将开票":
                self.driver.refresh()
                print('---尚未开售，刷新等待---')
                continue
            else:
                self.num += 1  # 记录抢票轮数
                self.choose_date()
                print("###日期和票价选择成功###")

    def choose_pos(self):
        print("###开始选座###")
        # while self.driver.title.find('确认订单') == -1:  # 如果跳转到了确认界面就算这步成功了，否则继续执行此步

        while True:

            seats_container = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "seat-container")))
            seats = []

            while len(seats) == 0:
                seats = seats_container.find_elements_by_css_selector('i')

            print("可选座位数", len(seats))
            ticket = 0
            for i in range(round(len(seats)/2)):
                seat = seats[i]
                if seat.get_attribute("style").find('not-allowed') == -1:
                    seat.click()
                    print("choose position " + seat.get_attribute('id'))
                    ticket += 1
                    if ticket == self.ticket_num:
                        break
            # 如果无座位
            if ticket == 0:
                print("无座位可选")
                self.driver.refresh()
            else:
                # self.driver.refresh()
                print("!!!!!!!!!!!有位置了!!!!!!!!!")
                break

        # click pay
        c_btn = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="target"]/div/div[4]/button')))
        c_btn.click()

        print("###选座成功###")

    def choose_user(self):
        print("###开始确认订单###")

        print("###填写取票人姓名###")
        receiver_input = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "#pane-second > div > div.el-row > div > form > div:nth-child(1) > div > div > input")))
        receiver_input.clear()
        receiver_input.send_keys(self.receiver)
        print("###填写观看人###")
        viewer_container = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#app > div > div > div > div.frame-body.mg-t-30 > div:nth-child(3)")))
        viewer_list = viewer_container.find_elements_by_class_name('film-viewer-wrapper')

        for i in range(len(viewer_list)):
            print("选择第", i, "个观演人")

            while 1:
                try:
                    viewer_btn = viewer_list[self.viewer[1]].find_element_by_tag_name('button')
                    viewer_btn.click()
                    break
                except Exception as e:

                    print(e, "重试实名选人")

            viewer_id_container = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "#app > div > div > div > div:nth-child(4) > div > div.el-dialog__body")))
            viewer_row = []
            while len(viewer_row) == 0:
                viewer_row = viewer_id_container.find_elements_by_class_name('el-table__row')

            viewer_row[i].find_element_by_tag_name('span').click()
            self.driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[4]/div/div[3]/div/div[1]').click()

        print("###确认支付###")
        while 1:
            try:
                self.driver.find_element_by_css_selector(
                    '#app > div > div > div > div.frame-body.mg-t-30 > div.text-right.pd-t-20.mg-b-50 > div.disFlex.hor-right.mg-t-20 > div > button').click()
                break
            except Exception as e:
                print("重试确认")

        print("###请支付###")
        self.time_end = time()
        print("###用时: ", self.time_end - self.time_start, ' s')

    def finish(self):
        if self.status == 6:  # 说明抢票成功
            print("###经过%d轮奋斗，共耗时%f秒，抢票成功！请确认订单信息###" % (self.num, round(self.time_end - self.time_start, 3)))
        else:
            self.driver.quit()


if __name__ == '__main__':
    target_url = 'https://www.polyt.cn/show/594121812962119680/40/30551'
    date = [2, 5, 1, 4, 3, 0]
    target_price = [9, 8, 7, 6, 5]
    ticket_num = 2
    receiver = "郭小星"
    viewer = [0, 1]
    con = Concert(0, target_url, date, ticket_num, receiver, viewer, target_price)
    # while True:
    try:
        con.enter_concert()
        con.choose_ticket()
        con.choose_pos()
        con.choose_user()
    except Exception as e:
        print("抢票失败", e)
        con.driver.get(con.target_url)
