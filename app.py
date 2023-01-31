from flask import Flask, request, jsonify
import selectorlib
import json
import requests
import locale
import time as time
from dateutil import parser as dateparser
app = Flask(__name__)
extractor = selectorlib.Extractor.from_yaml_file('selectors.yml')

def month2mese(dataita):
    if "gennaio" in dataita:
        return dataita.replace("gennaio", "01")
    if "febbraio" in dataita:
        return dataita.replace("febbraio", "02")
    if "marzo" in dataita:
        return dataita.replace("marzo", "03")
    if "aprile" in dataita:
        return dataita.replace("aprile", "04")
    if "maggio" in dataita:
        return dataita.replace("maggio", "05")
    if "giugno" in dataita:
        return dataita.replace("giugno", "06")
    if "luglio" in dataita:
        return dataita.replace("luglio", "07")
    if "agosto" in dataita:
        return dataita.replace("agosto", "08")
    if "settembre" in dataita:
        return dataita.replace("settembre", "09")
    if "ottobre" in dataita:
        return dataita.replace("ottobre", "10")
    if "novembre" in dataita:
        return dataita.replace("novembre", "11")
    if "dicembre" in dataita:
        return dataita.replace("dicembre", "12")
    else:
        return "11 11 1991"

def scrapeit(url):    
    headers = {
        'authority': 'www.amazon.it',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'it-IT;q=0.9,it;q=0.8',
    }

    # Download the page using requests
    print("Downloading %s"%url)
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    # Pass the HTML of the page and create 
    data = extractor.extract(r.text,base_url=url)
    reviews = []
    for r in data['reviews']:
        r["product"] = data["product_title"]
        r['url'] = url
        if 'verified_purchase' in r:
            if 'Acquisto Verificato' in r['verified_purchase']:
                r['verified_purchase'] = True
            else:
                r['verified_purchase'] = False
        
        r['rating'] = r['rating'].split(' su')[0]

        date_posted = r['date'].split('il ')[-1]
        if r['images']:
            r['images'] = "\n".join(r['images'])
        
        date_posted = month2mese(date_posted)
        print(date_posted)

        r['date'] = dateparser.parse(date_posted).strftime('%d %m %Y')
        reviews.append(r)
    histogram = {}
    for h in data['histogram']:
        histogram[h['key']] = h['value']
    data['histogram'] = histogram
    
    data['average_rating'] = float(data['average_rating'].split(' su')[0].replace(",","."))

    data['reviews'] = reviews
    #data['number_of_reviews'] = int(data['number_of_reviews'].split('  customer')[0])
    return data 
    
def scrapeus(url):    
    headers = {
        'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests
    print("Downloading %s"%url)
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    # Pass the HTML of the page and create 
    data = extractor.extract(r.text,base_url=url)
    reviews = []
    for r in data['reviews']:
        r["product"] = data["product_title"]
        r['url'] = url
        if 'verified_purchase' in r:
            if 'Verified Purchase' in r['verified_purchase']:
                r['verified_purchase'] = True
            else:
                r['verified_purchase'] = False
        r['rating'] = r['rating'].split(' out of')[0]
        date_posted = r['date'].split('on ')[-1]
        if r['images']:
            r['images'] = "\n".join(r['images'])
        r['date'] = dateparser.parse(date_posted).strftime('%d %b %Y')
        reviews.append(r)
    histogram = {}
    for h in data['histogram']:
        histogram[h['key']] = h['value']
    data['histogram'] = histogram
    data['average_rating'] = float(data['average_rating'].split(' out')[0])
    data['reviews'] = reviews
    #data['number_of_reviews'] = int(data['number_of_reviews'].split('  customer')[0])
    return data 


@app.route('/')
def api():
    url = request.args.get('url',None)
    if url:
        data = scrapeit(url)
        return jsonify(data)
    return jsonify({'error':'URL to scrape is not provided'}),400

@app.route('/us')
def usapi():
    url = request.args.get('url',None)
    if url:
        data = scrapeus(url)
        return jsonify(data)
    return jsonify({'error':'URL to scrape is not provided'}),400


@app.route("/npages")
def napi():
    url = request.args.get('url',None)
    if url:
        
        data = scrapeit(url)
        nexturl = data['next_page']
        
        for i in range(2):
            if(nexturl):
                additionaldata = scrapeit(nexturl)
                reviewschunk = additionaldata['reviews']
                nexturl = additionaldata['next_page']
                data['reviews'] = data['reviews'] + reviewschunk
        
        dumped = json.dumps(data)
        loaded_r = json.loads(dumped)
        return loaded_r
    return jsonify({'error':'URL to scrape is not provided'}),400

@app.route('/stanford')
def stanford_page():
    return """
      <h1>Hello stanford!</h1>

      <img src="https://maps.googleapis.com/maps/api/staticmap?size=700x300&markers=stanford" alt="map of stanford">
  
      <img src="https://maps.googleapis.com/maps/api/streetview?size=700x300&location=stanford" alt="street view of stanford">
    """

@app.route('/newyork')
def newyork_page():
    return """
      <h1>Hello newyork!</h1>

      <img src="https://maps.googleapis.com/maps/api/staticmap?size=700x300&markers=newyork" alt="map of newyork">
  
      <img src="https://maps.googleapis.com/maps/api/streetview?size=700x300&location=newyork" alt="street view of newyork">
      """