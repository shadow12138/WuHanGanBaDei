import json
import re
import os
from pyecharts.charts import Line, Pie, Map, Page
from pyecharts import options as opts
from colour import Color


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

    else:
        json_array = get_province_data(month, day, province_name)

        data = []
        for province in json_array:
            data.append((province['provinceShortName'], province['confirmedCount']))
        data.sort(key=lambda x: -x[1])

    labels = [d[0] for d in data]
    counts = [d[1] for d in data]
    return labels, counts


def create_dir(root):
    if not os.path.exists(root):
        os.makedirs(root)


def get_html(month, day):
    import requests
    url = 'http://3g.dxy.cn/newh5/view/pneumonia'
    response = requests.get(url)
    html = str(response.content, 'UTF-8')
    html_file = open('htmls/%d%d.html' % (month, day), 'w', encoding='UTF-8')
    html_file.write(html)
    html_file.close()

    # 省份数据
    json_file = open('jsons/%d%d.json' % (month, day), 'w', encoding='UTF-8')
    matches = re.findall('\[[^>]+\]', html)
    for match in matches:
        try:
            json_array = json.loads(match)
            json_object = json_array[0]
            if 'provinceName' in json_object and json_object['provinceName'] == '湖北省':
                json_file.write(match)
                break
        except:
            continue
    json_file.close()

    # 总体统计数据
    total_statistic_file = open('jsons/%d%d-总计.json' % (month, day), 'w', encoding='UTF-8')
    matches = re.findall('\{"id":1,[^(>})]+\}', html)
    for match in matches:
        if "infectSource" in match:
            total_statistic_file.write(match)
            break
    total_statistic_file.close()


def draw_tendency(month, day):
    dates = ['1-22', '1-23', '1-24', '1-25', '1-26', '1-27', '1-28',
             '1-29', '1-30', '1-31', '2-01', '2-02', '2-04', '2-05', '2-06', '2-07', '2-08', '2-09', '2-10', '2-11']
    v0 = [131, 259, 444, 688, 769, 1771, 1459, 1737, 1982, 2102, 2590, 2829, 3235, 3887, 3143, 3399, 2656, 3062, 2478,
          2015]
    v1 = [69, 105, 180, 323, 371, 1291, 840, 1032, 1220, 1347, 1921, 2103, 2345, 3156, 2447, 2841, 2147, 2618, 2097,
          1638]
    v2 = [v0[i] - v1[i] for i in range(len(v0))]
    print(v2)
    c = (
        Line(init_opts=opts.InitOpts(width='1000px', height='500px'))
            .add_xaxis(dates)
            .add_yaxis("全国新增确诊病例", v0,
                       is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=4, color='#B44038'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#B44038', border_color="#B44038", border_width=5
                       ))
            .add_yaxis("湖北新增确诊病例", v1, is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=2, color='#4E87ED'),
                       label_opts=opts.LabelOpts(position='bottom'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#4E87ED', border_color="#4E87ED", border_width=3
                       ))
            .add_yaxis("其他省份新增病例", v2, is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=2, color='#F1A846'),
                       label_opts=opts.LabelOpts(position='bottom'),
                       itemstyle_opts=opts.ItemStyleOpts(
                           color='#F1A846', border_color="#F1A846", border_width=3
                       ))
            .set_global_opts(title_opts=opts.TitleOpts(title=""),
                             yaxis_opts=opts.AxisOpts(
                                 max_=5000,
                                 min_=100,
                                 type_="log",
                                 name="y",
                                 splitline_opts=opts.SplitLineOpts(is_show=True),
                                 is_scale=True,
                                 axisline_opts=opts.AxisLineOpts(is_show=False)
                             ))

    )
    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    c.render('%s/新增病例趋势图.html' % root)


def get_map(labels, counts, where, title, size, pieces):
    my_map = Map(init_opts=opts.InitOpts(width=size[0], height=size[1]))
    my_map.add("", [list(z) for z in zip(labels, counts)], where)
    my_map.set_series_opts(label_opts=opts.LabelOpts(font_size=8))
    my_map.set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        legend_opts=opts.LegendOpts(is_show=False),
        visualmap_opts=opts.VisualMapOpts(
            pieces=pieces,
            is_piecewise=True,
            is_show=False
        ),
    )
    return my_map


def draw_multiple_map(month, day):
    page = Page(layout=Page.SimplePageLayout)
    size = ('350px', '380px')

    # 全国疫情地图
    labels, counts = get_province_status(month, day)
    country_map = get_map(labels=labels, counts=counts,
                          title='全国-%s例' % get_total_statistic(month, day)['confirmedCount'], size=size, where='china',
                          pieces=get_default_pieces())
    page.add(country_map)

    # 已知城市名称
    defined_cities = [line.strip() for line in open('py_echarts_city_names.txt', 'r', encoding='UTF-8').readlines()]

    # 省份疫情地图
    for p in get_province_data(month, day):
        title = '%s-%d例' % (p['provinceShortName'], p['confirmedCount'])

        # 城市映射
        labels = []
        for city in p['cities']:
            name = city['cityName']
            if name.endswith('区'):
                labels.append(name)
            else:
                for d_name in defined_cities:
                    if len((set(d_name) & set(name))) == len(name):
                        if name == d_name:
                            labels.append(name + '市')
                        else:
                            labels.append(d_name)
                        break

        # 数量
        counts = [city['confirmedCount'] for city in p['cities']]
        if len(labels) == 0:
            continue

        pieces = get_pieces(min(counts), max(counts))
        province_map = get_map(labels=labels, counts=counts, title=title, size=size, where=p['provinceShortName'],
                               pieces=pieces)
        page.add(province_map)

    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    page.render('%s/省份地图.html' % root)


def get_pieces(min_value, max_value, ranges=10):
    colors = list(Color('#EE9678').range_to(Color('#B72D28'), ranges))
    step = (max_value - min_value) / ranges
    pieces = []
    for i in range(ranges):
        start, end = i * step + min_value, (i + 1) * step + min_value
        pieces.append({'min': start, 'color': colors[i].hex, 'max': None if end >= max_value else end})
    return pieces


def get_default_pieces():
    return [
        {'min': 1000, 'color': '#450704'},
        {'max': 999, 'min': 100, 'color': '#75140B'},
        {'max': 99, 'min': 10, 'color': '#AD2217'},
        {'max': 9, 'min': 1, 'color': '#DE605B'},
        {'max': 0, 'color': '#FFFEE7'},
    ]


def get_pie(labels, counts, title, size):
    pie = Pie(init_opts=opts.InitOpts(width=size[0], height=size[1]))
    pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False), title_opts=opts.TitleOpts(title))
    pie.add(
        title,
        [list(z) for z in zip(labels, counts)],
        radius=[5, 80],
    ).set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"), tooltip_opts=opts.TooltipOpts())
    return pie


def draw_multiple_pie(month, day):
    page = Page(layout=Page.SimplePageLayout)
    labels, counts = get_province_status(month, day)
    page.add(
        get_pie(labels, counts, '全国-%s例' % get_total_statistic(month, day)['confirmedCount'], size=('360px', '330px')))
    for p in get_province_data(month, day):
        title = '%s-%d例' % (p['provinceShortName'], p['confirmedCount'])
        labels = [city['cityName'] for city in p['cities']]
        counts = [city['confirmedCount'] for city in p['cities']]
        if len(labels) == 0:
            continue
        page.add(get_pie(labels, counts, title, size=('350px', '320px')))

    root = 'html-charts/%d%d' % (month, day)
    create_dir(root)
    page.render('%s/省份信息.html' % root)


if __name__ == '__main__':
    m, d = 2, 12
    # get_html(m, d)
    draw_tendency(m, d)
    draw_multiple_pie(m, d)
    draw_multiple_map(m, d)
