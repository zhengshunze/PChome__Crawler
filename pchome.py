{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "from datetime import datetime, timedelta\n",
    "import time \n",
    "import re\n",
    "import requests\n",
    "from bs4 import BeautifulSoup\n",
    "from pytz import timezone,utc\n",
    "import json\n",
    "import urllib.request\n",
    "from urllib.parse import urlparse\n",
    "import os\n",
    "from uuid import UUID, uuid4, uuid5"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "DOMAIN = 'https://ecshweb.pchome.com.tw'\n",
    "\n",
    "UUID_NAMESPACE = os.environ.get('UUID_NAMESPACE') or '91461c99-f89d-49d2-af96-d8e2e14e9b58'\n",
    "UUID_NS = UUID(UUID_NAMESPACE)\n",
    "\n",
    "def uuid(my_str=None):\n",
    "    uuid_obj=None\n",
    "    if my_str is None:\n",
    "        uuid_obj = uuid4()\n",
    "    else:\n",
    "        uuid_obj = uuid5(UUID_NS, my_str)\n",
    "    return str( uuid_obj )\n",
    "\n",
    "def brand(brand_code):\n",
    "    menu_url = 'https://ecapi.pchome.com.tw/cdn/ecshop/cateapi/v1.5/store&id={}'.format(brand_code)\n",
    "    resp = requests.get(menu_url).text\n",
    "    doc = json.loads(resp)\n",
    "    for i in doc: name = i['Name'].replace('●','').replace('★','').replace('▼','').replace('◆','').replace('■','').replace('　└►','').replace('➔','').replace('➽','').replace('▌','').replace('☑','').replace('❱','').replace('》','').replace('．','').replace('►','').replace('♀','').replace('♂','').replace('\\u3000','')\n",
    "    return(name)\n",
    "\n",
    "def category(brand_code):\n",
    "    code = brand_code[:4]\n",
    "    cat_url = 'https://ecapi.pchome.com.tw/cdn/ecshop/cateapi/v1.5/region&region={}&_callback=cb_ecshopCategoryRegion'.format(code)\n",
    "    resp = requests.get(cat_url).text\n",
    "    resp = resp.split('ecshopCategoryRegion(')[1].split(');}catch(e)')[0]\n",
    "    doc = json.loads(resp)\n",
    "    category = doc['Name']\n",
    "    return(category)\n",
    "\n",
    "def getPchomekey(keyword):\n",
    "    data={}\n",
    "    data['keyword used'] = keyword\n",
    "    data['Access Type'] = 'keyword search'\n",
    "    data['Section'] = 'Regular'\n",
    "    data['Section Order'] = '1'\n",
    "    data['etailer'] = 'PChome'\n",
    "    \n",
    "    parseAllPagination(data, keyword)\n",
    "    \n",
    "def parseAllPagination(data, keyword):\n",
    "    ty_url = DOMAIN + '/search/v3.3/all/results?q={}'.format(keyword)\n",
    "    resp = requests.get(ty_url).text\n",
    "    doc = json.loads(resp)  \n",
    "    numPage = doc['totalPage']\n",
    "    data['# of SKU'] = doc['totalRows']\n",
    "    for num in range(1, numPage+1):\n",
    "        pg_url = ty_url + '&page={}&sort=sale/dc'.format(str(num))\n",
    "        data['Page'] = num\n",
    "        parseList(pg_url, data, num)\n",
    "        \n",
    "def parseList(pg_url, data, num):\n",
    "    print(pg_url)\n",
    "    resp = requests.get(pg_url).text\n",
    "    doc = json.loads(resp)\n",
    "    position = 0\n",
    "    count = 0\n",
    "    \n",
    "    for product in doc['prods']:\n",
    "        data['Description'] = product['name']\n",
    "        pro_id = product['Id']\n",
    "        data['PrdCode'] = pro_id\n",
    "        article_url = 'https://24h.pchome.com.tw/prod/' + product['Id']\n",
    "        data['url'] = article_url\n",
    "        \n",
    "        if num == 1: position = position + 1\n",
    "        else:\n",
    "            count = count + 1\n",
    "            position = ((num - 1) * 20) + count\n",
    "        data['position_section'] = position\n",
    "        data['position_total'] = data['position_section']\n",
    "        \n",
    "        parseArticle(pro_id, data) \n",
    "    \n",
    "def parseArticle(pro_id, data):\n",
    "    pg_id = pro_id + '-000'\n",
    "    pg_url = 'https://24h.pchome.com.tw/ecapi/ecshop/prodapi/v2/prod?id={}&fields=Price,Store,isArrival24h'.format(pg_id)\n",
    "    resp = requests.get(pg_url).text\n",
    "    time.sleep(2)\n",
    "    doc = json.loads(resp)\n",
    "    \n",
    "    if not len(doc) == 0:\n",
    "        data['Selling Price'] = doc[pg_id]['Price']['P']\n",
    "        data['List Price'] = doc[pg_id]['Price']['M']\n",
    "        if data['List Price'] == 0: data['List Price'] = doc[pg_id]['Price']['P']\n",
    "    \n",
    "        brand_code = doc[pg_id]['Store']\n",
    "        data['Brand'] = brand(brand_code)\n",
    "        \n",
    "        if doc[pg_id]['isArrival24h'] == 1:\n",
    "            data['route'] = 'PChome>線上購物>24h購物>{}>{}'.format(category(brand_code), brand(brand_code))\n",
    "        else:\n",
    "            data['route'] = 'PChome>線上購物>購物中心>{}>{}'.format(category(brand_code), brand(brand_code))\n",
    "       \n",
    "        if re.search(r'/DJ', data['url']):\n",
    "            data['route'] = 'PChome24h書店>{}>{}>{}'.format(category(brand_code), brand(brand_code), data['Description'])\n",
    "    \n",
    "        crawler_tm = datetime.now(tz=timezone('Asia/Taipei'))\n",
    "        data['rtime'] = datetime.strftime(crawler_tm, '%Y-%m-%d %H:%M:%S')\n",
    "        data['ID'] = uuid(pg_url)\n",
    "        data['Out of Stock'] = 0\n",
    "        \n",
    "        pro_url = 'https://ecapi.pchome.com.tw/cdn/marketing/order/v2/prod/activity?prodid='.format(pg_id)\n",
    "        resp2 = requests.get(pro_url).text\n",
    "        doc2 = json.loads(resp2)\n",
    "        for promotion in doc2:\n",
    "            data['promotion tag'] = [ i['Name'] for i in promotion['Activity'] ]\n",
    "    \n",
    "    else:\n",
    "        data['Selling Price'] = ''\n",
    "        data['List Price'] = ''\n",
    "        data['Description'] = ''\n",
    "        data['Brand'] = ''\n",
    "        data['route'] = ''\n",
    "        data['rtime'] = ''\n",
    "        data['ID'] = ''\n",
    "        data['Out of Stock'] = 1\n",
    "    \n",
    "    print(data)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {
    "scrolled": true
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "請輸入關鍵字:NBA球衣\n",
      "https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=NBA球衣&page=1&sort=sale/dc\n",
      "{'keyword used': 'NBA球衣', 'Access Type': 'keyword search', 'Section': 'Regular', 'Section Order': '1', 'etailer': 'PChome', '# of SKU': 98, 'Page': 1, 'Description': 'NBA NIKE 巫師隊 John Wall 球衣 (AJ4650-010)', 'PrdCode': 'DEBNRR-A9009TOAF', 'url': 'https://24h.pchome.com.tw/prod/DEBNRR-A9009TOAF', 'position_section': 1, 'position_total': 1, 'Selling Price': 1090, 'List Price': 2680, 'Brand': '└NBA OUTLET', 'route': 'PChome>線上購物>24h購物>運動服>└NBA OUTLET', 'rtime': '2020-06-27 16:42:32', 'ID': '5dd7a5dc-5272-5d2f-b5e2-8c60d2c8d005', 'Out of Stock': 0}\n",
      "{'keyword used': 'NBA球衣', 'Access Type': 'keyword search', 'Section': 'Regular', 'Section Order': '1', 'etailer': 'PChome', '# of SKU': 98, 'Page': 1, 'Description': 'NBA NIKE 拓荒者 Damian Lillard 球衣 (AJ4640-010)', 'PrdCode': 'DEBNRR-A900AH9J5', 'url': 'https://24h.pchome.com.tw/prod/DEBNRR-A900AH9J5', 'position_section': 2, 'position_total': 2, 'Selling Price': 1715, 'List Price': 2680, 'Brand': '└NBA OUTLET', 'route': 'PChome>線上購物>24h購物>運動服>└NBA OUTLET', 'rtime': '2020-06-27 16:42:35', 'ID': 'ac7d9f1a-9c75-5ed0-87e2-e63855c2823f', 'Out of Stock': 0}\n",
      "{'keyword used': 'NBA球衣', 'Access Type': 'keyword search', 'Section': 'Regular', 'Section Order': '1', 'etailer': 'PChome', '# of SKU': 98, 'Page': 1, 'Description': '(Youth Boys)NBA NIKE 青年版 SWINGMAN JERSEY 騎士隊 JAMES LeBRON 球迷版球衣 (WZ2B7BZ2P-CAVALIERS)', 'PrdCode': 'DEBNWY-A900AH7KC', 'url': 'https://24h.pchome.com.tw/prod/DEBNWY-A900AH7KC', 'position_section': 3, 'position_total': 3, 'Selling Price': 790, 'List Price': 2380, 'Brand': '└NBA青年版專區', 'route': 'PChome>線上購物>24h購物>運動服>└NBA青年版專區', 'rtime': '2020-06-27 16:42:38', 'ID': 'd3839de2-9f11-5241-976c-c38564d071b8', 'Out of Stock': 0}\n"
     ]
    },
    {
     "ename": "KeyboardInterrupt",
     "evalue": "",
     "output_type": "error",
     "traceback": [
      "\u001b[1;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[1;31mKeyboardInterrupt\u001b[0m                         Traceback (most recent call last)",
      "\u001b[1;32m<ipython-input-5-e1a24ceb312d>\u001b[0m in \u001b[0;36m<module>\u001b[1;34m()\u001b[0m\n\u001b[0;32m      1\u001b[0m \u001b[0mkeyword\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0minput\u001b[0m\u001b[1;33m(\u001b[0m\u001b[1;34m\"請輸入關鍵字:\"\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m----> 2\u001b[1;33m \u001b[0mgetPchomekey\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mkeyword\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m",
      "\u001b[1;32m<ipython-input-2-f9d6a6f6c3b5>\u001b[0m in \u001b[0;36mgetPchomekey\u001b[1;34m(keyword)\u001b[0m\n\u001b[0;32m     36\u001b[0m     \u001b[0mdata\u001b[0m\u001b[1;33m[\u001b[0m\u001b[1;34m'etailer'\u001b[0m\u001b[1;33m]\u001b[0m \u001b[1;33m=\u001b[0m \u001b[1;34m'PChome'\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     37\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m---> 38\u001b[1;33m     \u001b[0mparseAllPagination\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mdata\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mkeyword\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m\u001b[0;32m     39\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     40\u001b[0m \u001b[1;32mdef\u001b[0m \u001b[0mparseAllPagination\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mdata\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mkeyword\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m:\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n",
      "\u001b[1;32m<ipython-input-2-f9d6a6f6c3b5>\u001b[0m in \u001b[0;36mparseAllPagination\u001b[1;34m(data, keyword)\u001b[0m\n\u001b[0;32m     48\u001b[0m         \u001b[0mpg_url\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mty_url\u001b[0m \u001b[1;33m+\u001b[0m \u001b[1;34m'&page={}&sort=sale/dc'\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0mformat\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mstr\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mnum\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     49\u001b[0m         \u001b[0mdata\u001b[0m\u001b[1;33m[\u001b[0m\u001b[1;34m'Page'\u001b[0m\u001b[1;33m]\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mnum\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m---> 50\u001b[1;33m         \u001b[0mparseList\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpg_url\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mdata\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mnum\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m\u001b[0;32m     51\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     52\u001b[0m \u001b[1;32mdef\u001b[0m \u001b[0mparseList\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpg_url\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mdata\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mnum\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m:\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n",
      "\u001b[1;32m<ipython-input-2-f9d6a6f6c3b5>\u001b[0m in \u001b[0;36mparseList\u001b[1;34m(pg_url, data, num)\u001b[0m\n\u001b[0;32m     71\u001b[0m         \u001b[0mdata\u001b[0m\u001b[1;33m[\u001b[0m\u001b[1;34m'position_total'\u001b[0m\u001b[1;33m]\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mdata\u001b[0m\u001b[1;33m[\u001b[0m\u001b[1;34m'position_section'\u001b[0m\u001b[1;33m]\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     72\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m---> 73\u001b[1;33m         \u001b[0mparseArticle\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpro_id\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mdata\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m\u001b[0;32m     74\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     75\u001b[0m \u001b[1;32mdef\u001b[0m \u001b[0mparseArticle\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpro_id\u001b[0m\u001b[1;33m,\u001b[0m \u001b[0mdata\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m:\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n",
      "\u001b[1;32m<ipython-input-2-f9d6a6f6c3b5>\u001b[0m in \u001b[0;36mparseArticle\u001b[1;34m(pro_id, data)\u001b[0m\n\u001b[0;32m     77\u001b[0m     \u001b[0mpg_url\u001b[0m \u001b[1;33m=\u001b[0m \u001b[1;34m'https://24h.pchome.com.tw/ecapi/ecshop/prodapi/v2/prod?id={}&fields=Price,Store,isArrival24h'\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0mformat\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpg_id\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     78\u001b[0m     \u001b[0mresp\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mrequests\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0mget\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mpg_url\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0mtext\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m---> 79\u001b[1;33m     \u001b[0mtime\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0msleep\u001b[0m\u001b[1;33m(\u001b[0m\u001b[1;36m2\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m\u001b[0;32m     80\u001b[0m     \u001b[0mdoc\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mjson\u001b[0m\u001b[1;33m.\u001b[0m\u001b[0mloads\u001b[0m\u001b[1;33m(\u001b[0m\u001b[0mresp\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     81\u001b[0m \u001b[1;33m\u001b[0m\u001b[0m\n",
      "\u001b[1;31mKeyboardInterrupt\u001b[0m: "
     ]
    }
   ],
   "source": [
    "keyword = input(\"請輸入關鍵字:\") \n",
    "getPchomekey(keyword)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'keyword used': 'NBA球衣',\n",
       " 'Access Type': 'keyword search',\n",
       " 'Section': 'Regular',\n",
       " 'Section Order': '1',\n",
       " 'etailer': 'PChome',\n",
       " '# of SKU': 98,\n",
       " 'Page': 1,\n",
       " 'Description': 'NBA NIKE 巫師隊 John Wall 球衣 (AJ4650-010)',\n",
       " 'PrdCode': 'DEBNRR-A9009TOAF',\n",
       " 'url': 'https://24h.pchome.com.tw/prod/DEBNRR-A9009TOAF',\n",
       " 'position_section': 1,\n",
       " 'position_total': 1,\n",
       " 'Selling Price': 1090,\n",
       " 'List Price': 2680,\n",
       " 'Brand': '└NBA OUTLET',\n",
       " 'route': 'PChome>線上購物>24h購物>運動服>└NBA OUTLET',\n",
       " 'rtime': '2020-06-27 16:42:32',\n",
       " 'ID': '5dd7a5dc-5272-5d2f-b5e2-8c60d2c8d005',\n",
       " 'Out of Stock': 0}"
      ]
     },
     "execution_count": 11,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "bb = dict({'keyword used': 'NBA球衣', 'Access Type': 'keyword search', 'Section': 'Regular', 'Section Order': '1', 'etailer': 'PChome', '# of SKU': 98, 'Page': 1, 'Description': 'NBA NIKE 巫師隊 John Wall 球衣 (AJ4650-010)', 'PrdCode': 'DEBNRR-A9009TOAF', 'url': 'https://24h.pchome.com.tw/prod/DEBNRR-A9009TOAF', 'position_section': 1, 'position_total': 1, 'Selling Price': 1090, 'List Price': 2680, 'Brand': '└NBA OUTLET', 'route': 'PChome>線上購物>24h購物>運動服>└NBA OUTLET', 'rtime': '2020-06-27 16:42:32', 'ID': '5dd7a5dc-5272-5d2f-b5e2-8c60d2c8d005', 'Out of Stock': 0})\n",
    "\n",
    "bb"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.6.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}