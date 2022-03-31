import time
from urllib import response
import httpx
import bs4
import re

from mongo import save_data
from config import get_config

# url: https://www.sehuatang.org/forum-103-1.html
# url2: https://www.sehuatang.org/forum.php?mod=forumdisplay&fid=103&typeid=480&filter=typeid&typeid=480&page=2
# $Env:http_proxy="http://127.0.0.1:11223";$Env:https_proxy="http://127.0.0.1:11223"
# proxy = "http://127.0.0.1:11223"

# 获取帖子的id(访问板块)
def get_plate_info(fid: int, page: int, proxy, date_time):
    """
    :param fid: 板块id
    :param page: 页码
    :param proxy: 代理服务器地址
    :param date_time: 日期，格式: 2019-01-01

    :return: info_list
    """
    print("get plate " + str(fid) + " page " + str(page))
    url = "https://www.sehuatang.org/forum.php"
    # 参数
    params = {
        "mod": "forumdisplay",
        "fid": fid,
        "page": page,
    }

    response = httpx.get(url, params=params, proxies=proxy)
    # 使用bs4解析
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    all = soup.find_all(id=re.compile("^normalthread_"))
    # 存放字典的列表
    info_list = []
    for i in all:
        data = {}
        title_list = i.find("a", class_="s xst").get_text().split(" ")
        number = title_list[0]
        title_list.pop(0)
        title = " ".join(title_list)
        date = i.find("span", attrs={"title": re.compile("^" + date_time)})
        if date is None:
            continue
        id = i.find(class_="showcontent y").attrs["id"].split("_")[1]
        data["number"] = number
        data["title"] = title
        data["date"] = date.attrs["title"]
        data["tid"] = id
        info_list.append(data)
    return info_list


# print(get_page_info())


# 访问每个帖子的页面
def get_page(tid, proxy):
    """
    :param tid: 帖子id
    """
    data = {}
    print("get page " + tid)
    url = "https://www.sehuatang.org/forum.php?mod=viewthread&tid={}".format(tid)
    response = httpx.get(url, proxies=proxy)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    # 获取帖子的标题
    title = soup.find("h1", class_="ts").find("span").get_text()
    # 发布时间
    post_time = (
        soup.find("img", class_="authicn vm")
        .parent.find("em")
        .find("span")
        .attrs["title"]
    )
    # 楼主发布的内容
    info = soup.find("td", class_="t_f")
    # 存放图片的列表
    img_list = []
    for i in info.find_all("img"):
        img_list.append(i.attrs["file"])
    # 磁力链接
    magnet = soup.find("div", class_="blockcode").find("li").get_text()

    data["title"] = title
    data["post_time"] = post_time
    data["img"] = img_list
    data["magnet"] = magnet

    return data


def main():
    # 获取配置
    config = get_config()
    # 获取板块id
    fid_list = config["sehuatang"]["fid"]
    # 获取页码
    page_num = config["sehuatang"]["page_num"]
    # 获取日期
    date_time = config["sehuatang"]["date"]
    # print(type(date_time))
    if date_time is None:
        date_time = time.strftime("%Y-%m-%d", time.localtime())
    else:
        date_time = date_time.strftime("%Y-%m-%d")
    # 代理服务器
    proxy_enable = config["proxy"]["proxy_enable"]
    if proxy_enable:
        proxy = config["proxy"]["proxy_host"]
    else:
        proxy = None

    # 循环抓取所有页面
    info_list_all = []
    for fid in fid_list:

        for page in range(1, page_num + 1):
            info_list = get_plate_info(fid, page, proxy, date_time)
            info_list_all.extend(info_list)

        data_list = []
        for i in info_list_all:
            try:
                data = get_page(i["tid"], proxy)
                data["number"] = i["number"]
                data["title"] = i["title"]
                data["date"] = i["date"]
                data["tid"] = i["tid"]
                post_time = data["post_time"]
                # 再次匹配发布时间（因为页面获取的时间可能不准确）
                if re.match("^" + date_time, post_time):
                    data_list.append(data)
                # data_list.append(data)
            except Exception as e:
                print(e)
                continue
            finally:
                continue
        save_data(data_list, fid)


if __name__ == "__main__":
    main()