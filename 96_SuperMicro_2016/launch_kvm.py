#!/usr/bin/env python

import time
import sys
import logging

from selenium import webdriver

LOGGER = logging.getLogger(__name__)

def open_kvm(hostname, socks_port=1080):
    chrome_options = webdriver.ChromeOptions()

    # Use Socks and disable the certificate check
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:{}'.format(socks_port))
    chrome_options.add_argument('--host-resolver-rules=\"MAP * ~NOTFOUND , EXCLUDE 127.0.0.1\"')


    cc = webdriver.Chrome(chrome_options=chrome_options)
    cc.set_window_size(1024, 768)

    # Login
    cc.get("https://{}".format(hostname))
    cc.find_element_by_xpath('//input[@name = "name"]').send_keys("ADMIN")
    cc.find_element_by_xpath('//input[@name = "pwd"]').send_keys("ADMIN")
    cc.find_element_by_xpath('//input[@name = "Login"]').click()
    time.sleep(10)               # Let things settle

    # Go to the KVM
    cc.get('https://{}/cgi/url_redirect.cgi?url_name=man_ikvm_html5_bootstrap'.format(hostname))
    time.sleep(2)

def main():

    logging.basicConfig(level=logging.WARN)
    # If this ends up being useful, we can do real args
    for host in sys.argv[1:]:
        hostname = "sm{}-ipmi".format(host)
        try:
            open_kvm(hostname)
        except:                 # If
            LOGGER.exception("Failed to connect to host %s", hostname)

    raw_input("Press enter to close browsers")

if __name__ == "__main__":
    main()
