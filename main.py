import time
import httpx
import bs4
import re

from mongo import save_data
from config import get_config
from log_util import TNLog

log = TNLog()


# 获取帖子的id(访问板块)
def get_plate_info(fid: int, page: int, proxy, date_time):
    """
    :param fid: 板块id
    :param page: 页码
    :param proxy: 代理服务器地址
    :param date_time: 日期，格式: 2019-01-01

    :return: info_list
    """
    log.info("Crawl the plate " + str(fid) + " page number " + str(page))
    url = "https://{}/forum.php".format(get_config("domain_name"))
    # 参数
    params = {
        "mod": "forumdisplay",
        "fid": fid,
        "page": page,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
        "cookie": "UM_distinctid=17de17aee1edd-006cbd7a1c99c7-4303066-1fa400-17de17aee1fd42; CNZZDATA1280511935=1432301821-1640160379-%7C1640853459; cPNj_2132_smile=1D1; cPNj_2132_saltkey=nIFGzacf; cPNj_2132_lastvisit=1648120917; cPNj_2132_atarget=1; cPNj_2132_visitedfid=103D145D39D36D106D151D107D2D38D152; High=fa8362d9f320d9a85b50de1b51093e77; cPNj_2132_lastfp=d021b67b8716f2f2cdf8caba1e7cfc29; cPNj_2132_lastact=1649221864%09forum.php%09forumdisplay; cPNj_2132_st_t=0%7C1649221864%7Cd66d2ced0dca736763e46bd0c8b31a2c; cPNj_2132_forum_lastvisit=D_104_1648712354D_37_1648815821D_152_1648818323D_38_1648818334D_2_1648818354D_107_1648856490D_151_1648856506D_106_1648856664D_36_1648856880D_39_1648856887D_103_1649221864",
    }

    response = httpx.get(url, headers=headers, params=params, proxies=proxy)
    # 使用bs4解析
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    all = soup.find_all(id=re.compile("^normalthread_"))
    # 存放字典的列表
    info_list = []
    tid_list = []
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
        tid_list.append(id)
    return info_list, tid_list


# 访问每个帖子的页面
def get_page(tid, proxy):
    """
    :param tid: 帖子id
    """
    data = {}
    # log.info("Crawl the page " + tid)
    url = "https://{}/forum.php?mod=viewthread&tid={}".format(
        get_config("domain_name"), tid
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
        "cookie": "UM_distinctid=17de17aee1edd-006cbd7a1c99c7-4303066-1fa400-17de17aee1fd42; CNZZDATA1280511935=1432301821-1640160379-%7C1640853459; cPNj_2132_smile=1D1; cPNj_2132_saltkey=nIFGzacf; cPNj_2132_lastvisit=1648120917; cPNj_2132_atarget=1; cPNj_2132_visitedfid=103D145D39D36D106D151D107D2D38D152; High=fa8362d9f320d9a85b50de1b51093e77; cPNj_2132_lastfp=d021b67b8716f2f2cdf8caba1e7cfc29; cPNj_2132_lastact=1649221864%09forum.php%09forumdisplay; cPNj_2132_st_t=0%7C1649221864%7Cd66d2ced0dca736763e46bd0c8b31a2c; cPNj_2132_forum_lastvisit=D_104_1648712354D_37_1648815821D_152_1648818323D_38_1648818334D_2_1648818354D_107_1648856490D_151_1648856506D_106_1648856664D_36_1648856880D_39_1648856887D_103_1649221864",
    }
    response = httpx.get(url, headers=headers, proxies=proxy)
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
    fid_list = config["sehuatang"]["fid"]
    page_num = config["sehuatang"]["page_num"]
    date_time = config["sehuatang"]["date"]

    if date_time is None:
        date_time = time.strftime("%Y-%m-%d", time.localtime())
    else:
        date_time = date_time.__str__()

    proxy_enable = config["proxy"]["proxy_enable"]
    if proxy_enable:
        proxy = config["proxy"]["proxy_host"]
    else:
        proxy = None

    # 循环抓取所有页面
    for fid in fid_list:
        info_list_all = []
        tid_list_all = []
        for page in range(1, page_num + 1):
            try:
                info_list, tid_list = get_plate_info(fid, page, proxy, date_time)
                info_list_all.extend(info_list)
                tid_list_all.extend(tid_list)
            except Exception as e:
                log.error(e)
                continue
            finally:
                continue
        log.info("即将开始爬取的页面 " + " ".join(tid_list_all))
        data_list = []
        tid_list = []
        for i in info_list_all:
            try:
                data = get_page(i["tid"], proxy)
                data["number"] = i["number"]
                data["title"] = i["title"]
                data["date"] = i["date"]
                data["tid"] = i["tid"]
                post_time = data["post_time"]
                # 再次匹配发布时间（因为上级页面获取的时间可能不准确）
                if re.match("^" + date_time, post_time):
                    data_list.append(data)
                    tid_list.append(data["tid"])
            except Exception as e:
                log.error("Crawl the page " + " ".join(list(i.values())) + " failed.")
                log.error(e)
                continue
            finally:
                continue
        log.info("本次抓取的数据条数为：" + str(len(data_list)) + " 分别为： " + " ".join(tid_list))
        log.info("开始写入数据库")
        save_data(data_list, fid)


if __name__ == "__main__":
    main()
