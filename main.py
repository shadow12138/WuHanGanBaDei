import matplotlib.pyplot as plt
import numpy as np
import json
from matplotlib.font_manager import FontProperties
import re
import os
from pyecharts.charts import Line, Pie, Map, Page
from pyecharts import options as opts


def get_province_data(month, day, province_name=None):
    file = open('jsons/%d%d.json' % (month, day), 'r', encoding='UTF-8')
    json_array = json.loads(file.read())
    file.close()

    if not province_name:
        return json_array

    for json_object in json_array:
        if json_object['provinceName'] == province_name:
            return json_object
        if json_object['provinceShortName'] == province_name:
            return json_object
    return None


def get_total_statistic(month, day):
    file = open('jsons/%d%d-总计.json' % (month, day), 'r', encoding='UTF-8')
    json_object = json.loads(file.read())
    file.close()
    return json_object


def get_province_status(month, day, province_name=None):
    if province_name:
        print(province_name)
        json_object = get_province_data(month, day, province_name)

        data = []
        for city in json_object['cities']:
            data.append((city['cityName'], city['confirmedCount']))
        data.sort(key=lambda x: -x[1])

        title = '%s2020年%d月%d日确诊病例' % (province_name, month, day)
    else:
        json_array = get_province_data(month, day, province_name)

        data = []
        for province in json_array:
            data.append((province['provinceShortName'], province['confirmedCount']))
        data.sort(key=lambda x: -x[1])

        title = '全国2020年%d月%d日确诊病例' % (month, day)

    labels = [d[0] for d in data]
    counts = [d[1] for d in data]
    return labels, counts, title


def show_province_status(month, day, province_name=None):
    labels, counts, title = get_province_status(month, day, province_name)
    # draw_pie(month, day, labels, counts, title)
    get_pyecharts_pie(month, day, labels, counts, title)


def draw_pie(month, day, labels, counts, title):
    if len(labels) == 0:
        return

    labels = np.array(labels)
    counts = np.array(counts)
    title += '-%d例' % sum(counts)
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    explode = np.zeros(len(labels))
    explode[np.argmax(counts)] = 0.1
    wedges, texts = ax.pie(counts,
                           wedgeprops=dict(width=0.5),
                           startangle=-40,
                           explode=explode)

    font = FontProperties(fname='font/ZiXinFangYunYuanTi-2.ttf')
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
              bbox=bbox_props, zorder=0, va="center",
              fontproperties=font)

    for i, p in enumerate(wedges[:6]):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate('%s-%d例' % (labels[i], counts[i]), xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                    horizontalalignment=horizontalalignment, **kw)

    ax.set_title(title, fontproperties=font)

    root = 'charts/%d%d' % (month, day)
    create_dir(root)
    plt.savefig('%s/%s.jpg' % (root, title))
    plt.show()


def create_dir(root):
    if not os.path.exists(root):
        os.makedirs(root)


def draw(month, day):
    provinces = get_province_data(month, day)
    for p in provinces:
        show_province_status(month, day, p['provinceShortName'])
    show_province_status(month, day)


def get_html(month, day):
    import requests
    url = 'http://3g.dxy.cn/newh5/view/pneumonia'
    response = requests.get(url)
    html = str(response.content, 'UTF-8')
    html_file = open('htmls/%d%d.html' % (month, day), 'w', encoding='UTF-8')
    html_file.write(html)
    html_file.close()

    json_file = open('jsons/%d%d.json' % (month, day), 'w', encoding='UTF-8')
    matches = re.findall('\[[^>]+\]', html)
    for match in matches:
        json_array = json.loads(match)
        json_object = json_array[0]
        if 'provinceName' in json_object and json_object['provinceName'] == '湖北省':
            json_file.write(match)
            break
    json_file.close()

    total_statistic_file = open('jsons/%d%d-总计.json' % (month, day), 'w', encoding='UTF-8')
    matches = re.findall('\{"id":1,[^(>})]+\}', html)
    for match in matches:
        if "infectSource" in match:
            total_statistic_file.write(match)
            break
    total_statistic_file.close()


def compare(m1, d1, m2, d2):
    ps1 = get_province_data(m1, d1)
    ps2 = get_province_data(m2, d2)
    ps_dict1 = {}
    ps_dict2 = {}
    for p in ps1:
        ps_dict1[p['provinceShortName']] = p['confirmedCount']
    for p in ps2:
        ps_dict2[p['provinceShortName']] = p['confirmedCount']

    data = []
    for key in ps_dict2:
        increased_count = ps_dict2[key]
        if key in ps_dict1:
            increased_count -= ps_dict1[key]
        data.append((key, increased_count))
    data.sort(key=lambda x: -x[1])

    labels = [d[0] for d in data]
    counts = [d[1] for d in data]
    title = '2020年%d月%d日全国新增确诊病例' % (m2, d2)
    draw_pie(m2, d2, labels, counts, title)
    get_pyecharts_pie(m2, d2, labels, counts, title)


def get_pyecharts_pie(month, day, labels, counts, title, size=None):
    if title.find('全国') != -1 and title.find('新增') == -1:
        title += '-%d例' % get_total_statistic(month, day)['confirmedCount']
    else:
        title += '-%d例' % (sum(counts))

    if not size:
        pie = Pie(init_opts=opts.InitOpts(width='1200px', height='700px'))
        pie.add(
            "",
            [list(z) for z in zip(labels, counts)],
            radius=["40%", "80%"],
            center=['50%', '60%'],

        )
        pie.set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            legend_opts=opts.LegendOpts(
                orient="vertical", pos_top="15%", pos_left="2%"
            ),
        )
    else:
        pie = Pie(init_opts=opts.InitOpts(width=size[0], height=size[1]))
        pie.add(
            "",
            [list(z) for z in zip(labels, counts)],
            radius=[5, 80],

        )
        pie.set_global_opts(
            title_opts=opts.TitleOpts(title='全国-%d例' % get_total_statistic(month, day)['confirmedCount']),
            legend_opts=opts.LegendOpts(
                is_show=False
            ),
        )

    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    pie.render('%s/%s.html' % (root, title))
    return pie


def draw_tendency(month, day):
    dates = ['1-22', '1-23', '1-24', '1-25', '1-26', '1-27', '1-28',
             '1-29', '1-30', '1-31', '2-01', '2-02']
    v0 = [131, 259, 444, 688, 769, 1771, 1459, 1737, 1982, 2101, 2602, 2829]

    v1 = [69, 105, 180, 323, 371, 1291, 840, 1032, 1221, 1347, 1921, 2590, 2103]
    v2 = [v0[i] - v1[i] for i in range(len(v0))]
    c = (
        Line(init_opts=opts.InitOpts(width='800px', height='500px'))
            .add_xaxis(dates)
            .add_yaxis("全国新增确诊病例", v0,
                       is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=4, color='#B44038'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#B44038', border_color="#B44038", border_width=5
                       ))
            .add_yaxis("湖北新增确诊病例", v1, is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=2, color='#6FA0A7'),
                       label_opts=opts.LabelOpts(position='bottom'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#6FA0A7', border_color="#6FA0A7", border_width=3
                       ))
            .add_yaxis("其他省份新增病例", v2, is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=2, color='#F9DB51'),
                       label_opts=opts.LabelOpts(position='bottom'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#F9DB51', border_color="#F9DB51", border_width=3
                       ))
            .set_global_opts(title_opts=opts.TitleOpts(title=""),
                             yaxis_opts=opts.AxisOpts(
                                 max_=3000,
                                 min_=100,
                                 type_="log",
                                 name="y",
                                 splitline_opts=opts.SplitLineOpts(is_show=True),
                                 is_scale=True,
                                 axisline_opts=opts.AxisLineOpts(is_show=False)
                             ))
        # .set_series_opts(areastyle_opts=opts.AreaStyleOpts(opacity=0.5))

    )
    c.render('charts/%d%d-新增病例趋势图.html' % (month, day))
    return c


def draw_map(month, day, size=None):
    labels, counts, title = get_province_status(month, day, None)
    total_count = get_total_statistic(month, day)['confirmedCount']

    if not size:
        country_map = Map()
    else:
        country_map = Map(init_opts=opts.InitOpts(width=size[0], height=size[1]))

    country_map.add("", [list(z) for z in zip(labels, counts)], "china")
    country_map.set_global_opts(
        title_opts=opts.TitleOpts(title="2020年%d月%d日全国确诊病例-%s例" % (month, day, total_count)),
        visualmap_opts=opts.VisualMapOpts(
            pieces=[
                {'min': 1000, 'color': '#450704'},
                {'max': 999, 'min': 100, 'color': '#75140B'},
                {'max': 99, 'min': 10, 'color': '#AD2217'},
                {'max': 9, 'min': 1, 'color': '#DE605B'},
                {'max': 0, 'color': '#FFFEE7'},
            ],
            is_piecewise=True
        ),
    )

    country_map.render('charts/%d%d-疫情地图.html' % (month, day))
    return country_map


def draw_multiple_pie(month, day):
    max_width, max_height = 1400, 3000
    pie = Pie(init_opts=opts.InitOpts(width='{}px'.format(max_width), height='{}px'.format(max_height)))
    pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False),
                        title_opts=opts.TitleOpts(title='2020-%02d-%d 全国各省份城市确诊病例' % (month, day)))

    h_center, v_center = 10, 40
    horizontal_step, vertical_step = 350, 320
    for p in get_province_data(month, day):
        title = '%s-%d例' % (p['provinceShortName'], p['confirmedCount'])
        labels = [city['cityName'] for city in p['cities']]
        counts = [city['confirmedCount'] for city in p['cities']]
        if len(labels) == 0:
            continue
        pie.add(
            title,
            [list(z) for z in zip(labels, counts)],
            radius=[5, 80],
            center=[h_center + 150, v_center + 110]
        ).set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"), tooltip_opts=opts.TooltipOpts())

        h_center += horizontal_step
        if h_center + 200 > max_width:
            h_center = 10
            v_center += vertical_step

    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    pie.render('%s/省份信息.html' % root)


def draw_multiple_map(month, day):
    page = Page(layout=Page.SimplePageLayout)
    width, height = '350px', '380px'
    page.add(draw_map(month, day, size=(width, height)))
    city_map = {"西双版纳": "西双版纳傣族自治州", "大理": "大理白族自治州", "红河": "红河哈尼族自治州", "德宏": "德宏傣族景颇族自治州",
                "甘孜州": "甘孜藏族自治州", "凉山州": "凉山彝族自治州", "阿坝州": "阿坝藏族羌族自治州",
                "黔东南州": "黔东南苗族侗族自治州", "黔西南州": "黔西南依族苗族自治州", "黔南州": "黔南布依族苗族自治州",
                "湘西自治州": "湘西土家族苗族自治州", "恩施州": "恩施土家族苗族自治州", "恩施": "恩施土家族苗族自治州", "神农架林区": "神农架林区"}
    for p in get_province_data(month, day):
        title = '%s-%d例' % (p['provinceShortName'], p['confirmedCount'])

        # 城市
        labels = []
        for city in p['cities']:
            city_name = city['cityName']
            if city_name in city_map:
                labels.append(city_map[city_name])
            elif p['provinceShortName'] in ['重庆', '上海', '北京', '天津']:
                labels.append(city_name)
            else:
                labels.append(city_name + "市")

        # 数量
        counts = [city['confirmedCount'] for city in p['cities']]
        if len(labels) == 0:
            continue
        province_map = Map(init_opts=opts.InitOpts(width=width, height=height))
        province_map.add("", [list(z) for z in zip(labels, counts)], p['provinceShortName'])
        province_map.set_series_opts(label_opts=opts.LabelOpts(font_size=8))
        province_map.set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            legend_opts=opts.LegendOpts(is_show=False),
            visualmap_opts=opts.VisualMapOpts(
                pieces=[
                    {'min': 1000, 'color': '#450704'},
                    {'max': 999, 'min': 500, 'color': '#75140B'},
                    {'max': 499, 'min': 200, 'color': '#AD2217'},
                    {'max': 199, 'min': 10, 'color': '#DE605B'},
                    {'max': 9, 'color': '#FFFEE7'},
                ],
                is_piecewise=True,
                is_show=False
            ),
        )
        page.add(province_map)

    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    page.render('%s/省份地图.html' % root)


def draw_multiple_pie_02(month, day):
    page = Page(layout=Page.SimplePageLayout)
    width, height = '350px', '320px'
    labels, counts, title = get_province_status(month, day)
    page.add(get_pyecharts_pie(month, day, labels, counts, title, size=('360px', '330px')))
    for p in get_province_data(month, day):
        title = '%s-%d例' % (p['provinceShortName'], p['confirmedCount'])
        labels = [city['cityName'] for city in p['cities']]
        counts = [city['confirmedCount'] for city in p['cities']]
        if len(labels) == 0:
            continue
        pie = Pie(init_opts=opts.InitOpts(width=width, height=height))
        pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False), title_opts=opts.TitleOpts(title))
        pie.add(
            title,
            [list(z) for z in zip(labels, counts)],
            radius=[5, 80],
        ).set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"), tooltip_opts=opts.TooltipOpts())
        page.add(pie)

    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    page.render('%s/省份信息.html' % root)


if __name__ == '__main__':
    m, d = 2, 3
    # get_html(m, d)
    # draw(m, d)
    # compare(2, 2, 2, 3)
    draw_tendency(m, d)
    # draw_map(m, d)
    # draw_multiple_pie(m, d)
    # draw_multiple_pie_02(m, d)
    # draw_multiple_map(m, d)
