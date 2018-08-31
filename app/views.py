import os
import platform
import random
import time
from datetime import datetime

from PIL import Image, ImageChops
from django.http import JsonResponse
from django.shortcuts import render
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from docsend_scraper.settings import MEDIA_ROOT, BASE_DIR


def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((50, 50)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -10)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def savepdf(request):

    try:

        # Check if it exists
        url = request.POST.get('url', '')
        emailad = request.POST.get('emailad', '')
        emailpass = request.POST.get('emailpass', '')

        ID = url[url.rfind('/') + 1:]

        # START PROCESS
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # driver = webdriver.Chrome(chrome_options=chrome_options,
        #                           executable_path=r'C:\Utility\BrowserDrivers\chromedriver.exe')
        if platform.system() == "Darwin":
            # browser = webdriver.Chrome(r'./chromedriver')
            browser = webdriver.Chrome(r'./chromedriver')
        else:
            # browser = webdriver.Chrome(r'./chromedriver_linux', chrome_options=chrome_options)
            browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=chrome_options)
            # browser = webdriver.Chrome(executable_path=BASE_DIR + './chromedriver_linux', chrome_options=chrome_options)

        browser.get(url)

        time.sleep(1)
        try:
            element = WebDriverWait(browser, 4).until(EC.presence_of_element_located((By.ID, "youtube-modal")))
        except:
            print("Fail")

        email_ID = ''
        try:
            email_ID = browser.find_element_by_name('visitor[email]')
            email_ID.send_keys(emailad)
        except:
            print("Email not required")

        time.sleep(1)
        try:
            pass_ID = browser.find_element_by_name('visitor[passcode]')
            pass_ID.send_keys(emailpass)
        except:
            print("Password not required")

        time.sleep(1)
        try:
            email_ID.send_keys(Keys.TAB)
            email_ID.send_keys(Keys.ENTER)
        except:
            print("---")

        exitflag = 0
        browser.switch_to_active_element().send_keys(Keys.RIGHT)

        pages = None
        while exitflag == 0:
            # click right until no blank pagescheck until pages stabilizes
            browser.switch_to_active_element().send_keys(Keys.RIGHT)
            time.sleep(0.4 + random.randint(1, 100) / 100)
            pages = browser.find_elements_by_css_selector(".preso-view.page-view")
            urls = []
            for x in pages:
                urls.append(x.get_attribute("src"))
            if any("blank.gif" in s for s in urls):
                exitflag = 0
            else:
                exitflag = 1

        urls = []
        for x in pages:
            urls.append(x.get_attribute("src"))

        c = 1
        for x in urls:
            browser.get(x)
            browser.save_screenshot("AX{}.png".format(c))
            c = c + 1

        imagelist = []
        for i in range(1, c):
            imagelist.append("AX{}.png".format(i))

        time.sleep(10)  # befor 10 sec
        for img in imagelist:
            im = Image.open(img)
            im = trim(im)
            im.save(img)

        im = Image.open(imagelist[0])
        wheight = im.size[0]
        wwidth = im.size[1]
        im.close()

        pdf = FPDF("L", "pt", [wwidth, wheight])
        pdf.set_margins(0, 0, 0)

        for image in imagelist:
            pdf.add_page()
            pdf.image(image, 0, 0)

        for i in imagelist:
            os.remove(i)

        cdir = os.getcwd()
        browser.close()

        pdfname = '{}_{}.pdf'.format(ID, datetime.now().date().strftime('%Y%m%d_%H%M%S'))
        pdf.output(os.path.join(MEDIA_ROOT, pdfname))

        # This is to serve the file in a normal function based view
        # pdf_file = open(os.path.join(MEDIA_ROOT, pdfname), 'rb')
        # response = HttpResponse(pdf_file, content_type='application/pdf')
        # response['Content-Disposition'] = "attachment; filename={}".format(pdfname)

        # Returning in this way because it will be the response for an AJAX call
        return JsonResponse({'downloadUrl': os.path.join('media', pdfname)})

    except Exception as ex:
        return JsonResponse({'error': ex.__str__()})


def index(request):
    return render(request, 'index.html', {'title': 'DocSend Scraper (Beta)'})
