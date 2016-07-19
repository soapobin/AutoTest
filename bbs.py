#!/usr/bin/env python
# coding:utf8
from selenium import webdriver
import time
import sys
import random

class Test:
	def __init__(self,url,username,password,title,content):
		self.url = url
		self.username = username
		self.password = password
		self.title = title
		self.content = content

	def loginUrl(self):
		#Solver Chrome ignore-certificate-errors Problem
		options = webdriver.ChromeOptions()
		options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
		global browser
		browser = webdriver.Chrome(executable_path='C:\Program Files (x86)\Google\Chrome\Application\chrome\chromedriver',chrome_options=options)
		browser.get(self.url)
		time.sleep(5)
		try:
			browser.find_element_by_xpath("//*[@id='uname']").send_keys(self.username)
			print "输入用户名正确!"
		except Exception,e:
			print e
			print "输入用户名失败!"
		time.sleep(2)
		#Sign in the password
		try: 
			browser.find_element_by_xpath("//*[@id='upwd']").send_keys(self.password)
			print "输入密码成功!"
		except Exception,e:
			print e
			print "输入密码失败!"
		time.sleep(2)
		#Click to login
		try:
			browser.find_element_by_xpath("//*[@id='loginButton']").click()
			print '登陆成功!'
		except Exception,e:
			print e
			print '登陆失败!'
		time.sleep(3)


	def getSession(self):
		#get the session cookie  
		cookie = [item["name"] + "=" + item["value"] for item in browser.get_cookies()]  
		# print cookie 


	def issueTopic(self):
		#进入子版块
		try:
			browser.find_element_by_xpath("//*[@id='pgt']/div/span[2]/a").click()
			time.sleep(2)
			# browser.find_element_by_xpath("//*[@id='newspecial']/img").click()
			time.sleep(1)
			print "进入结婚干货区成功!"
		except Exception, e:
			print e
			print "进入结婚干货区失败!"
		time.sleep(3)


	def writeTopic(self):
		#发布话题
		try:
			browser.find_element_by_xpath("//*[@id='subject']").send_keys(self.title)
			time.sleep(2)
			browser.switch_to_frame("e_iframe")
			time.sleep(1)
			browser.find_element_by_xpath("html/body").send_keys(self.content)
			browser.switch_to_default_content()
			time.sleep(2)
			browser.find_element_by_xpath("//*[@id='postsubmit']").click()
			time.sleep(1)
			print "发帖成功!"
		except Exception,e:
			print e
			print "发帖失败!"
		time.sleep(3)

if __name__=="__main__":
	title = "Test" + str(random.randint(1,1000))
	content = str(random.random()*100000)
	ceshi = Test(url="bbs.xxxxxx.com",username="13600011001",password=123456,title=title,content=content)
	ceshi.loginUrl()
	ceshi.issueTopic()




