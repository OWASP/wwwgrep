# **************************************************************
# Revision 1.1 2021 Mark Deen.           
# **************************************************************
from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urlparse
from requests_html import HTMLSession
import argparse
import requests
import re
from os.path import exists

result_list=[]					# ALL RESULTS IN A SEARCH
complete_url_list=[]			# ALL URLS LOADED FROM FILE OR SCOPE
js_list=[]						# PER RUN LIST USED IN JSOFFPAGE ANALYSIS

proxysetting = {
  "http"  : None,				# HTTP PROXY
  "https" : None				# HTTPS PROXY
}

header = {
	"User-Agent": None,			# SET USER AGENT
	"Authorization": None,		# SET AUTHORIZATION TOKEN
	"User-Custom-Header": None	# CUSTOM TOKEN FOR USER
}

# SEARCH TYPES
get_rel_links=False				# GET RELATIVE LINKS
get_abs_links=False				# GET ABSOLUTE LINKS
get_input_fields=False			# GET LIST OF INPUT FIELDS
search_scripts=False			# GET LIST OF SCRIPTS
search_hidden=False				# GET LIST OF HIDDEN FIELDS
search_visible_text=False		# GET LIST OF VISIBLE TEXT (NOT JS)
search_comments=False			# SEARCH DEV COMMENTS
search_java_offpage=False		# SEARCH OFFPAGE (LINKED) JS ALSO
meta_search=False				# SEARCH META
find_header=False				# FIND TEXT IN HEADER
find_header_value=False			# FIND TEXT IN HEADER VALUE
search_all=False				# FIND IN ALL
is_regex=False					# FIND REGEX

# FLAGS 
deduplicate=False				# DEDUPLICATE RESULTS
case_sensitive=False			# CONTROLS CASE SENSITIVE SEARCHES
allow_redirects=False			# DETERMINE IF REDIRECTS ARE SUPPORTED
recursive=False					# DETERMINE IF SITE RECURSION IS SUPPORTED
this_root_only=False			# DETERMINE THE SCOPE OF RECURSION
java_render=False				# TURN JAVA RENDERING ON OR OFF
include_base_in_results=True    # DETERMINES IF THE URL IS INCLUDED IN OUTPUT

# OPTIONS
separator=":"					# SEPARATOR FOR OUTPUT - CHANGEABLE VIA CLI PARAMETER

# INTERNAL TYPES
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def element_is_visible(element):
	# RETURNS FLAG IF AN ELEMENT IS VISIBLE OR NOT
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True
    
def clean_string(string_to_clean):
	# REMOVES UNDESIRED CHARACTERS FROM A STRING
	return str(string_to_clean).translate(str.maketrans('', '', ' \n\t\r'))
	
def is_url(url):
	# DETERMINES IF A URL IS PROPERLY FORMATTED OR NOT
	try:
		result = urlparse(url)
		return all([result.scheme, result.netloc])
	except ValueError:
		return False

def get_root(url):
	try:
		result = urlparse(url)
		return result.netloc
	except ValueError:
		return False

def read_urls_from_file(filename):
	# READS THE URLS FROM A SPECIFIED FILE
	global urls_from_file

	urls_from_file=[]

	if exists(filename):
		urls_file = open(filename, "r")
		file_line = urls_file.readline().strip()
		while file_line:
			if str(file_line).strip() != "":
				if is_url(file_line):
					complete_url_list.append(file_line)
				else:
					print(style.RED+"This does not appear to be a valid URL: "+style.RESET+"["+str(file_line).strip()+"]")
			file_line = urls_file.readline().strip()

		urls_file.close()  
	
def if_append(in_listobject, search_string, url_arg, separator):
	# PLACES RESULTS IN A LIST FOR OUTPUT, PERFORMS FORMATTING AND CASE CHECKING
	global is_regex 
	global result_list
	
	for item in in_listobject:

		# DETERMINE IF WE ARE LOOKING AT A REGEX OR TEXT SEARCH

		if not include_base_in_results:
			url_arg=""
			separator=""

		if is_regex:
		# IS A REGEX PATTERN - TREAT SEARCH AS A REGEX STRING
			try:
				# MAKE SURE THE REGEX IS CLEAN
				regex_pattern = re.compile("{0}".format(search_string))
				#regex_pattern = re.compile(search_string)
			except: 
				# ERROR IF NOT
				print(style.RED+"This does not appear to be a valid RegEX: "+style.RESET+"["+str(search_string).strip()+"]")
				exit()

			# PROCESS REGEX
			if re.search(regex_pattern,str(item)):
				# ADD REGEX FIND
				result_list.append(str(url_arg).strip()+str(separator)+clean_string(item).strip())

		else:
		# NOT A REGEX - TREAT SEARCH AS A STRING
			
			# DETERMINE CASE SENSITIVITY
			if not case_sensitive:
				# NON CASE SENSITIVE
				search_string = str(search_string).upper().strip()
				item = str(item).upper().strip()
				recorded_item=str(item).strip()
			else:
				# CASE SENSITIVE
				search_string = str(search_string).strip()
				item = str(item).strip()
				recorded_item=str(item).strip()

			# DETERMINE IF DE-DUPLICATION IS REQUIRED
			if search_string in item:
				if deduplicate:
					# DE-DUPLICATION REQUESTED
					if search_string not in result_list:
						result_list.append(str(url_arg).strip()+str(separator)+clean_string(recorded_item).strip())
				else:
					# ALLOW DUPLICATES PER PAGE
					result_list.append(str(url_arg).strip()+str(separator)+clean_string(recorded_item).strip())
		

def plan_recursion(url_arg, in_listobject):
	# BUILDS THE LIST FOR FURTHER RECURSION, THE INPUT IS THE 
	# OUTPUT OF response.html.absolute_links
	global this_root_only
	global complete_url_list

	for result_url in in_listobject:

		if is_url(result_url):
			# VALID URL
			url_cleaned=str(url_arg).upper().strip()
			url_result=str(result_url).upper().strip()
			root=str(get_root(url_arg)).upper().strip()
			result_root=str(get_root(result_url)).upper().strip()

			if this_root_only:
				if root == result_root:
					if url_result not in complete_url_list:
						# CHECK IF THIS URL IS ALREADY IN THE LIST
						if url_result != url_cleaned: 
							# MAKE SURE WE ARE NOT ADDING OUR CURRENT URL
							complete_url_list.append(url_result)

			else:
				if url_result not in complete_url_list:
					if url_result != url_cleaned: 
						complete_url_list.append(url_result)


def get_url(url_arg):
		session = HTMLSession()
		try:
			# TRY TO OBTAIN A RESPONSE OBJECT
			response = session.get(url_arg, proxies=proxysetting, headers=header, allow_redirects=allow_redirects)
			try:
				# OBTAIN THE RESPONSE CODE	
				response.raise_for_status()
			except requests.RequestException as reqe:
				# DISPLAY AN ERROR IF SO RAISED
				print(style.RED+"ERROR >>>> Unable to connect to target please verify your URL, proxy settings, header settings and if you need to allow redirects"+style.RESET)
				print(style.RED+"ERROR >>>> "+str(reqe.request)+" RESPONSE: "+str(reqe.response)+style.RESET)
				return
		except Exception as e_message:
			# DID NOT RECIEVE A RESPONSE OBJECT
			print(style.RED+"ERROR >>>> Initializing Python HTMLSession"+style.RESET)
			print(e_message)
			return

		return response


def get_raw_response(url_arg,search_string=None):
	# THE COMPLETE URL LIST AS READ FROM CLI FILE ARG
	global complete_url_list
	global separator
	global recursive
	global this_root_only
	global java_render
	global js_list
	
	response=""

	# PERFORM HTTP GET
	response=get_url(url_arg)

	if response is not None:
			
		# ENTER OPTIONS

		# TURN JAVA RENDERING OFF IF SELECTED
		if java_render:
		 	response.html.render()

		if find_header or find_header_value:
		 	# EXAMINE FOR PRESENCE OF TEXT IN HEADER 

		 	for head,val in response.headers.items():

		 		# CHECK CASE SENSITIVITY
		 		if case_sensitive:
		 			search = str(search_string).strip()
		 			head = str(head).strip()
		 			val = str(val).strip()
		 		else:
		 			search_string = str(search_string).upper().strip()
		 			head = str(head).upper().strip()
		 			val = str(val).upper().strip()
		 			url_arg=str(url_arg).upper().strip()

		 		# STRIP OUT THE BASE URL IF NOT REQUIRED
	 			if not include_base_in_results:
	 				url_arg=""
	 				separator=""

		 		if find_header:
		 			# SEARCH IN HEADER STRUCTS (AS TEXT COMPARE)
		 			if search_string in head:
		 				result_list.append(url_arg+str(separator)+head+":"+val)

		 		if find_header_value:
		 			# SEARCH IN VALUE (AS TEXT COMPARE)
		 			if search_string in val:
		 				result_list.append(url_arg+str(separator)+head+":"+val)

		
		if get_rel_links:
			# GET RELATIVE LINKS
			links = response.html.links
			if_append(links,search_string, url_arg, str(separator))

		if get_abs_links:
			# GET ABSOLUTE LINKS FROM PAGE - ADDED A IF NOT RECURSIVE
			# TO PREVENT URLS THAT ARE OFF ROOT FROM BEING RE-ADDED 
			links = response.html.absolute_links
			if_append(links,search_string, url_arg, str(separator))
		
		if get_input_fields:
		 	# GET ALL INPUT FIELDS ON A PAGE
		 	parser = 'html5lib'
		 	soup = BeautifulSoup(response.text, parser)
		 	if_append(soup.find_all("input"),search_string, url_arg, str(separator))

		if search_scripts:
		 	# OBTAIN ALL SCRIPTS ON THIS PAGE ONLY
	 		parser = 'html5lib'
	 		soup = BeautifulSoup(response.text, parser)
	 		if_append(soup.find_all('script'),search_string, url_arg, str(separator))

		 	if search_java_offpage:
		 		# WE ARE LOOKING AT ALL LINKED JS SCRIPTS ALSO SO ADD TO THE PAGE CONTENT FINDINGS
		 		parser = 'html5lib'
		 		soup = BeautifulSoup(response.text, parser)
		 		# PARSE THE PAGE CONTENT LOOKING FOR THE LINKED SRC TAGS
		 		if soup is not None:
		 			script_src=soup.find_all('script',{"src":True})
			 		for source in script_src:
			 			# SOME RECURSION HERE
			 			jsurl=str(source['src']).upper().strip()
			 			if jsurl not in js_list and jsurl is not None:
			 				# ADD TO THE DE-DUPE LIST
			 				js_list.append(str(source['src']).upper().strip())
			 				jsurl=str(source['src']).strip()

			 				# THIS IS POSSIBLY A LINK WITHOUT SCHEMA
			 				if jsurl.startswith("//"):
			 					jsurl="https:"+jsurl

			 				# THIS IS POSSIBLY A LINK TO THE LOCAL URL ON THE SERVER
			 				if jsurl.startswith("/"):
			 					try:
			 						url_parts=urlparse(url_arg)
			 					except Exception as e:
			 						print(style.RED+"ERROR >>>> Obtaining URL for recursive JavaScript retrieval"+style.RESET)
			 						print(e_message)
			 						return None

			 					if not str(url_parts.netloc).endswith("/"):
			 						jsurl=url_parts.scheme+"://"+url_parts.netloc+"/"+jsurl
			 					else:
			 						jsurl=url_parts.scheme+"://"+url_parts.netloc+jsurl
			 					
			 				if get_url(jsurl) is not None:
			 					jstext=clean_string(get_url(jsurl).text)
			 					if jstext is not None:
			 						if_append(jstext.split(),search_string, url_arg+" (LINKED-SCRIPT)", str(separator))


		if search_visible_text:
		 	# SEARCH VISIBLE TEXT ON A PAGE
		 	parser = 'html5lib'
		 	soup = BeautifulSoup(response.text, parser)
		 	texts = soup.findAll(text=True)
		 	visible_texts = filter(element_is_visible, texts)
		 	page_text = u" ".join(t.strip() for t in visible_texts)
		 	if_append(str(page_text).split(),search_string, url_arg, str(separator))
						
		if search_comments:
		 	# SEARCH COMMENTS LEFT BY DEVELOPERS
		 	parser = 'html5lib'
		 	soup = BeautifulSoup(response.text, parser)
		 	if_append(soup.find_all(string=lambda text: isinstance(text, Comment)),search_string, url_arg, str(separator))

		if meta_search:
		 	# SEARCH META TAGS ON A PAGE
		 	if_append(response.html.find('meta'),search_string, url_arg, str(separator))

		if search_hidden:
		 	# SEARCH HIDDEN FIELDS ON A PAGE
			parser = 'html5lib'
			soup = BeautifulSoup(response.text, parser)
			if_append(soup.find_all("input", type="hidden"),search_string, url_arg, str(separator))

		if search_all:
			# SEARCH THE ENTIRE PAGE CONTENT REGARDLESS OF TAG
			if_append(str(response.text).split(), search_string, url_arg, str(separator))

		# PLAN FOR RECURSION ONCE EVENTS ABOVE HAVE BEEN PROCESSED ONCE
		if recursive:
			plan_recursion(url_arg, response.html.absolute_links)


		return result_list
		

def main():

	# URL LIST
	global complete_url_list

	# OPERATIONS
	global get_rel_links
	global get_abs_links
	global get_input_fields
	global search_scripts
	global search_visible_text
	global search_comments
	global search_java_offpage
	global meta_search
	global search_all
	global find_header
	global find_header_value
	global search_hidden
	
	# Switches 
	global case_sensitive
	global deduplicate
	global allow_redirects
	global include_base_in_results
	global recursive
	global this_root_only
	global java_render
	
	# Options
	global separator
	global proxysetting
	global header
	global is_regex
	# The dependent variable is search which
	# will be interpreted as a regEx string

	# LOCALS FOR ARGPARSE
	https_proxy=""
	http_proxy=""
	user_agent=""
	auth_header=""
	search_string=""
	

	parser = argparse.ArgumentParser()

	# Process Flags
	parser.add_argument("-i", "--ignore-case", help="Performs case insensitive search",action="store_false",dest='case_sensitive', default=True)
	parser.add_argument("-d", "--dedupe", help="Prevent duplicates per page checked",action="store_false", dest='deduplicate', default=True)
	parser.add_argument("-r", "--no-redirects", help="Do not follow redirects",action="store_false", dest='allow_redirects', default=True)
	parser.add_argument("-b", "--no-base-url", help="Prevent base URL in output",action="store_false", dest='include_base_in_results', default=True)
	parser.add_argument("-x", "--regex", help="Treat search argument as RegEX",action="store_true", dest='is_regex', default=False)
	parser.add_argument("-j", "--java-render", help="Turn on JavaScript rendering of HTML objects",action="store_true", dest='java_render', default=False)
	parser.add_argument("-p", "--linked-js-on", help="Turn on searching of SRC linked JavaScripts",action="store_true", dest='java_offpage', default=False)
	
	# RECURSION PLAN
	recursion = parser.add_mutually_exclusive_group()
	recursion.add_argument("-rr", "--recurse-root", help="Recursively search site (or sites) staying on the root domain",action="store_true", dest='recurse_root', default=False)
	recursion.add_argument("-ra", "--recurse-any", help="Recursively search site (or sites) including off domain links",action="store_true", dest='recurse_any', default=False)

	# INCLUDE OPTIONALS
	parser.add_argument('-e', "--separator", action='store',dest='separator', type=str, help="String used to separate the URL from the finding default is :", default=" : ")
	parser.add_argument('-ps', "--https-proxy", action='store',dest="https_proxy", type=str, help="HTTPS Proxy setting")
	parser.add_argument('-pp', "--http-proxy", action='store',dest="http_proxy", type=str, help="HTTP Proxy setting")
	parser.add_argument('-hu', "--user-agent", action='store',dest="user_agent", type=str, help="Specify user agent in requests")
	parser.add_argument('-ha', "--auth-header", action='store',dest="auth_header", type=str, help="Specify authorization header in requests")

	# SEARCH PARAM
	parser.add_argument(dest='search_string', type=str, help="Text to find on URLs")

	# TARGET PARAMETER
	target = parser.add_mutually_exclusive_group(required=True)
	target.add_argument('-t', '--target', dest="target", type=str, help="Target URL for search")
	target.add_argument('-f', '--file', dest="file", type=str, help="Text file containing list of URLs")

	# GET SEARCH PARAMETERS
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-sr", "--relative", help="Return page links as relative URLS", action="store_true", dest="get_rel_links", default=False)
	group.add_argument("-sa", "--absolute", help="Return page links as absolute URLS", action="store_true", dest="get_abs_links", default=False)
	group.add_argument("-si", "--input-fields", help="Return page input fields", action="store_true", dest="get_input_fields", default=False)
	group.add_argument("-ss", "--scripts", help="Return matches found in scripts", action="store_true", dest="search_scripts", default=False)	
	group.add_argument("-st", "--text", help="Return matches found in visible text", action="store_true", dest="search_visible_text", default=False)
	group.add_argument("-sc", "--comments", help="Return matches found in developer comments", action="store_true", dest="search_comments", default=False)
	group.add_argument("-sm", "--meta", help="Return matches found in page meta tags", action="store_true", dest="meta_search", default=False)
	group.add_argument("-sf", "--hidden", help="Return matches in hidden page fields", action="store_true", dest="search_hidden", default=False)
	group.add_argument("-s", "--all", help="Return matches anywhere in html content", action="store_true", dest="search_all", default=False)
	group.add_argument("-sh", "--header-name", help="Return matches in response header names", action="store_true", dest="find_header", default=False)
	group.add_argument("-sv", "--header-value", help="Return matches in response header values", action="store_true", dest="find_header_value", default=False)

	# Parse and print the results
	args = parser.parse_args()

	# THESE FOR FUTURE WORK

	# MAPPING TO GLOBALS - FLAGS
	case_sensitive=args.case_sensitive
	deduplicate=args.deduplicate
	allow_redirects=args.allow_redirects
	include_base_in_results=args.include_base_in_results
	is_regex=args.is_regex
	java_render=args.java_render

	# MAPPING TO GLOBALS - OPTIONALS
	separator=args.separator
	proxysetting['https']=args.https_proxy
	proxysetting['http']=args.http_proxy
	header['user-agent']=args.user_agent
	header['authorization']=args.auth_header

	# MAPPING TO GLOBALS - SEARCH PARAMETERS
	search_all=args.search_all
	get_rel_links=args.get_rel_links
	get_abs_links=args.get_abs_links
	get_input_fields=args.get_input_fields
	search_scripts=args.search_scripts
	search_visible_text=args.search_visible_text
	search_comments=args.search_comments
	search_hidden=args.search_hidden
	search_java_offpage=args.java_offpage
	meta_search=args.meta_search
	find_header=args.find_header
	find_header_value=args.find_header_value

	# CLEAR GLOBAL
	complete_url_list=[]

	# CLEAR LOCAL
	output_results=[]

	if args.target:
		complete_url_list.append(args.target)

	# READ FILE IF PROVIDED
	if args.file:
		read_urls_from_file(args.file)

	# HANDLE RECURSION PROCESSING
	if args.recurse_root:
		this_root_only=True
		recursive=True

	if args.recurse_any:
		this_root_only=False
		recursive=True

	counter=0

	# HANDLE FILE AND RECURSIVE OPERATIONS

	for url in complete_url_list:
		counter=counter+1
		print("Testing: "+str(counter)+" of "+str(len(complete_url_list))+" items tested          ", end="\r")
		pending_results=get_raw_response(url,args.search_string)
		if pending_results is not None:
			output_results=output_results+pending_results

	# FINALLY OUTPUT THE RESULTS TO STDOUT

	if output_results is not None:
		for line in output_results:
	 		print(line)


if __name__ == "__main__": main()	

