#!/usr/bin/env python3
import pywikibot
from pywikibot import pagegenerators
import zhdialsyn as pwb_source

site = pywikibot.Site()
gen = pagegenerators.PrefixingPageGenerator('Module:zh/data/dial-syn/')
ignore_list = [
	'Module:zh/data/dial-syn/documentation',
	'Module:zh/data/dial-syn/template',
]

for page in gen:
	if page.title() in ignore_list:
		continue

	page = pwb_source.main(page)
	page.save('update with new locations')
