#-*- coding:utf-8 -*-

from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import sublime, sublime_plugin
import os
import re
import time


class GetDdlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print 'executing get_ddl'
		settings=innerProcessor.init()
		driver=webdriver.Chrome()
		innerProcessor.login(driver, settings.get('username').encode('utf-8'),settings.get('password').encode('utf-8'),settings.get('app_key').encode('utf-8'))
		#self.view.insert(edit, 0, "Hello, World!")
		selection=self.view.sel()[0]
		url=self.view.substr(selection)
		ddl=innerProcessor.getDDLFromUrl(driver, url) 
		self.view.replace(edit,selection,ddl.decode('utf-8'))
		driver.quit()

class CreateDatabaseCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		print 'executing create_database'
		settings=innerProcessor.init()
		self.view.run_command('selectAll')
		driver=webdriver.Chrome()
		innerProcessor.login(driver, settings.get('username').encode('utf-8'),settings.get('password').encode('utf-8'),settings.get('app_key').encode('utf-8'))
		sel=self.view.sel()[0]
		ddl=self.view.substr(sel)
		table=innerProcessor.ParseDDL(ddl)
		print table
		innerProcessor.AddPrivateDatabaseInHive(table,driver)
		driver.quit()


class innerProcessor():
	@staticmethod
	def init():
		return sublime.load_settings('CloudData-Taobao.sublime-settings')





	@staticmethod
	def login(driver, user, passwd,app_key):
		driver.get('https://login.taobao.com/member/login.jhtml?redirectURL=http://clouddata.taobao.com/ide/data.htm?spm=0.0.0.0.Zrhz8L&sub=true')
		print driver.title.encode('utf-8')
		driver.execute_script("document.querySelector('#J_SafeLoginCheck').click();")
		# driver.find_element_by_id('J_SafeLoginCheck').click()
		driver.execute_script("document.querySelector('#TPL_username_1').value= '%s';" % user)
		driver.execute_script("document.querySelector('#TPL_password_1').value= '%s';" % passwd)
		driver.execute_script("document.querySelector('#J_SubmitStatic').click();")

		# driver.find_element_by_id('TPL_username_1').send_keys(user)
		# driver.find_element_by_id('TPL_password_1').send_keys(passwd)
		# driver.find_element_by_id('J_SubmitStatic').click()
		
		wait = ui.WebDriverWait(driver, 30)
		wait.until(lambda driver:driver.find_element_by_css_selector("#settings > div.w_con > div > form > table > tbody > tr:nth-child(3) > td:nth-child(2) > input:nth-child(1)").is_displayed())

		print driver.title.encode('utf-8')
		if app_key is None or not app_key.strip():
			return
		print "app_key: %s" % app_key
		if(u'聚石塔数据引擎 - 用户设置' in driver.title):
			#选择合适的app_key
			select=Select(driver.execute_script("return document.querySelector('#J_app_list')"))
			# select.find_element_by_xpath("//option[@value='%s']" % app_key).click()
			select.select_by_value(app_key)
			driver.find_element_by_css_selector("#settings > div.w_con > div > form > table > tbody > tr:nth-child(3) > td:nth-child(2) > input:nth-child(1)").click()

	@staticmethod
	def getDDLFromUrl(driver, url):
		driver.get(url)
		html=driver.page_source.encode('utf-8')
		pattern=re.compile(r'<td>序号</td>\s*<td>字段</td>\s*<td>类型</td>\s*<td>属性</td>\s*<td width="300">描述信息</td>\s*</tr>\s*(?P<row><tr>([\s\S]*?)</tr>)+\s*</tbody></table>',re.M | re.S)
		# print html
		items=pattern.finditer(html)
		tbody=None
		for item in items:
			print 'match'
			tbody=item.group() 
		pattern=re.compile(r'<td>(?P<varible>\w*?)</td><td>\s+(?P<type>\w+)\s+</td>\s+<td>\s*\W+</td>\s+<td.*?>(?P<desc>.*?)</td>',re.M | re.S)
		items=pattern.finditer(tbody)
		ddl='\n'
		for item in items:
			# print 'match'
			# print item.groups()
			ddl+="%s %s COMMENT '%s',\n" % (item.group('varible'),item.group('type'),item.group('desc'))
		# print 'haha'	
		ddl =ddl[0:-2]
		# print ddl
		driver.quit()
		return ddl+"\n"


	@staticmethod
	def ParseDDL(ddl):
		table={}
		pattern=re.compile(r"create\s*table\s*(?P<table_name>[\w\.]*)\s*\((?P<cloumns>[\s\S]*)\)\s*comment\s*'(?P<table_comment>.*?)'\s*with\s*dbproperties\s*\((?P<properties>.*?)\)\s*(with\s*index\s*(?P<db_index>\([^\)]*\)))*", re.I | re.M | re.S)
		items=pattern.finditer(ddl)
		cloumns_region=None
		properites_region=None
		#开始分析总体的表结构
		for item in items:
			# print item.groups()©
			table['table_name']=item.group('table_name')
			cloumns_region=item.group('cloumns')
			table['table_comment']=item.group('table_comment')
			properites_region=item.group('properties')
			index_region=item.group('db_index')
			break
		print cloumns_region.encode('utf-8')
		#开始获得字段的信息
		cloumns=[]
		pattern=re.compile(r"(?P<cloumn_name>\w*)\s*(?P<type>\w*)\s*comment\s*'(?P<cloumn_comment>[^']*)'", re.I| re.M | re.S)
		# print cloumns_region.encode('utf-8')
		items=pattern.finditer(cloumns_region)
		for item in items:
			# print item.groups()
			cloumn={}
			cloumn['cloumn_name']=item.group('cloumn_name')
			cloumn['type']=item.group('type')
			cloumn['cloumn_comment']=item.group('cloumn_comment')
			cloumns.append(cloumn)
		table['cloumns']=cloumns
		#获得额外的标信息
		properties={}
		if(properites_region is not None):
			pattern=re.compile(r"'(?P<name>[^:']*)'\s*:\s*'*(?P<value>[^']*)'*", re.I | re.M | re.S)
			items=pattern.finditer(properites_region)
			for item in items:
				# one_property={}
				properties[item.group('name')]=item.group('value')
				# properties.append(one_property)
			table['properties']=properties
		#获得index信息
		index=[]
		if(index_region is not None):
			pattern=re.compile(r"'(?P<index_name>[^:']*)'\s*:\s*'*(?P<index_cloumn>[^']*)'*", re.I | re.M | re.S)
			items=pattern.finditer(index_region)
			for item in items:
				print "*****************"
				one_index={}
				one_index['index_name']=item.group('index_name')
				one_index['index_cloumn']=item.group('index_cloumn')
				index.append(one_index)
			table['db_index']=index
		return table

	@staticmethod
	def AddPrivateDatabaseInHive(table,driver):
		driver.get('http://clouddata.taobao.com/ide/data.htm?spm=0.0.0.0.z5D3p7')
		driver.switch_to_frame('frame_content_parent')
		root_div=driver.find_element_by_css_selector("body > div.z-page")
		print root_div


		root_id=root_div.get_attribute('id')[:-1]
		# print root_id
		# print "*********root_id is ********" % root_id
		script="document.querySelector('#%su > div > div').click();" % root_id
		print script
		driver.execute_script(script)
		wait = ui.WebDriverWait(driver, 30)
		wait.until(lambda driver:driver.find_element_by_css_selector("#%sh2" % root_id).is_displayed())

		#填写db类型
		
		# driver.execute_script("document.querySelector('').value=%s" % table['tablename'])
		select=Select(driver.execute_script("return document.querySelector('#%sh2');" % root_id))
		select.select_by_visible_text(table['properties']['db_style'])
		#填写表名
		table_name=table['table_name']
		if('pri_result.' in table_name):
			table_name=table_name[11:]
		elif('pri_temp.' in table_name):
			table_name=table_name[9:]
		elif('pri_upload.' in table_name):
			table_name=table_name[10:]

		#填写表名	
		input_ele=driver.execute_script("return document.querySelector('#%sn2');" % root_id)
		input_ele.clear()
		input_ele.send_keys(table_name)
		#选择主题
		select=Select(driver.execute_script("return document.querySelector('#%sq2');" % root_id))
		print table['properties']['theme'].encode('utf-8')
		select.select_by_visible_text(table['properties']['theme'])
		#选择二级主题
		time.sleep(3)
		print table['properties']['second_theme'].encode('utf-8')
		select=Select(driver.execute_script("return document.querySelector('#%st2');" % root_id))
		select.select_by_visible_text(table['properties']['second_theme'].encode('utf-8'))
		#填写数据保存周期
		if(table['properties']['export_time'] is not None):
			export_time=table['properties']['export_time']
			# print "******************%s" % export_time
			if(export_time in '7'):
				driver.execute_script("document.querySelector('body > div.z-window-modal.z-window-modal-shadow > div.z-window-modal-cl > div > div > div > div > div:nth-child(1) > div > div > table > tbody.z-rows > tr.z-row.z-row-over > td:nth-child(2) > div > span > span:nth-child(1) > input[type=\"radio\"]').click();")
			elif(export_time in '30'):
				driver.execute_script("document.querySelector('body > div.z-window-modal.z-window-modal-shadow > div.z-window-modal-cl > div > div > div > div > div:nth-child(1) > div > div > table > tbody.z-rows > tr:nth-child(5) > td:nth-child(2) > div > span > span:nth-child(2) > input[type=\"radio\"]').click();")
			else:
				driver.execute_script("document.querySelector('body > div.z-window-modal.z-window-modal-shadow > div.z-window-modal-cl > div > div > div > div > div:nth-child(1) > div > div > table > tbody.z-rows > tr:nth-child(5) > td:nth-child(2) > div > span > span:nth-child(3) > input[type=\"radio\"]').click();")
		#填写数据表的comment
		input_ele=driver.execute_script("return document.querySelector('#%s23');" % root_id)
		input_ele.clear()
		input_ele.send_keys(table['table_comment'])
		#开始准备添加字段了，hoho
		cloumns=table['cloumns']
		for cloumn in cloumns:
			# driver.execute_script("document.querySelector('#%sd3').value='%s';" % (root_id, cloumn['cloumn_name']))
			input_ele=driver.execute_script("return document.querySelector('#%sd3')" % root_id)
			input_ele.clear() #send_keys(Keys.COMMAND,'a')
			time.sleep(0.2)
			input_ele.send_keys(cloumn['cloumn_name'])
			select1=Select(driver.execute_script("return document.querySelector('#%sf3')" % root_id))
			select1.select_by_visible_text(cloumn['type'])
			input_comment=driver.execute_script("return document.querySelector('#%sh3')" % root_id)
			# input_comment.send_keys(Keys.COMMAND,"a")
			input_comment.clear()
			time.sleep(0.2)
			input_comment.send_keys(cloumn['cloumn_comment'])	
			input_ele.click()
			driver.execute_script("document.querySelector('#%sj3').click()" % root_id)
			# button_ele=driver.execute_script("return document.querySelector('#%sj3')"% root_id);
			# button_ele.click()
			time.sleep(2)
			
		#接下来是著名的index
		indexes=table['db_index']
		if(indexes is not None):
			for index in indexes:
				print index
				input_ele=driver.execute_script("return document.querySelector('#%ss3');" % root_id)
				input_ele.clear()
				input_ele.send_keys(index['index_name'])
				select1=Select(driver.execute_script("return document.querySelector('#%st3')" % root_id))
				select1.select_by_visible_text(index['index_cloumn'])
				driver.execute_script("document.querySelector('#%sw3').click()" % root_id)
				# break
				time.sleep(2)

		#可以保存了
		driver.execute_script("document.querySelector('#%s_4').click()" % root_id)
		time.sleep(3)

