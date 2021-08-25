# WWWGrep
# OWASP Foundation Web Respository

### Author: Mark Deen & Aditi Mohan

### Introduction
WWWGrep is a rapid search “grepping” mechanism that examines HTML elements by type and permits focused (single), multiple (file based URLs) and recursive (with respect to root domain or not) searches to be performed. Header names and values may also be recursively searched in this manner. WWWGrep was designed to help both breakers and builders to quickly examine code bases under inspection, some use cases and examples are shown below.

Installation

	git clone 
	pip3 install r requirements.txt
	python3 wwwgrep.py <arguments and parameters>

Dependencies (pip3 install -r requirements.txt) 

    - Python 3.5+
    - BeautifulSoup 4 
    - UrlLib.parse
    - requests_html
    - argparse
    - requests
    - re
    - os.path

### Breakers
- Quickly locate login pages by searching for input fields named “username” or “password” on a site an using a recursion flag 
- Quickly check headers for the use of specific technologies
- Quickly locate cookies and JWT tokens by search response headers 
- Use with a proxy tool to automate recursion through a set links rapidly
- Locate all input sinks on a page (or site) by search for input fields and parameter processing symbology
- Locate all developer comments on a page to identify commented out code (or To Do’s) 
- Quickly test consistency of site controls implemented during recursion (headers, HSTS, CSP etc)
- Quickly find vulnerable JavaScript code present in web pages
- Identify API tokens and access keys present in page code

### Builders
- Quickly test multiple sites under management for the use of vulnerable code
- Quickly test multiple sites under management for the use of vulnerable frameworks/technologies
- Find sites which may share a common codebase to determine the impact of flaws/vulnerabilities
- Find sites which share a common authentication token (header auth token) 
- Find sites which may contain developer comments for server hygiene purposes
      

### Command line switches

	wwwgrep.py [target/file] [search_string] [search params/criteria/recursion etc]
  
```
Search Inputs

search_string		Specify the string to search for or alternatively “” 
			for all objects of type specified in search parameters

-t	--target	Specify a single URL as a target for the search
-f	--file		Specify a file containing a list of URLs to search

Recursion

-rr	--recurse-root	Limits URL recursion to the domain provided in the target
-ra	--recurse-any	Allows recursion to extend beyond the domain of the target

Matching Criteria

-i	--ignore-case	Performs case insensitive matching (default is to respect case)
-d	--dedupe        Allow duplicate findings per page (default is to de-duplicate findings)
-r	--no-redirects	Do not allow redirects (default is to allow redirects)
-b	--no-base-url   Omit the URL of the match from the output (default is to include the URL)
-x	--regex         Allows the use of RegEX matches (search_string is treated as a RegEX, default is off) 
-e	--separator	Specify and output specifier (default is : ) 
-j	--java-render   Turns on JavaScript rendering of page objects and text (default is off) 
-p	--linked-js-on  Turns on searching of linked (script src tags) Java Script (default is off)

Request Parameters

-ps	--https-proxy	Specify a proxy for the HTTPS protocol in https://<ip>:<port> format
-pp 	--http-proxy	Specify a proxy for the HTTP protocol in http://<ip>:<port> format
-hu	--user-agent	Specify a string to use as the user agent in the request
-ha	--auth-header	Specify a bearer token or other auth string to use in the request header

Search Parameters

-s	--all		Search all page HTML and scripts for terms that match the search specification
-sr	--relative	Search page links that match the search specification as relative URLs
-sa	--absolute	Search page links that match the search specification as absolute URLs
-si	--input-fields	Search page input fields that match the search specification
-ss	--scripts	Search scripts tags that match the search specification
-st	--text          Search visible text on the page that matches the search specification
-sc	--comments      Search comments on the page that match the search specification
-sm	--meta          Search in page metadata for matches to the search specification
-sf	--hidden        Search in hidden fields for specific matches to the search specification
-sh	--header-name	Search response headers for specific matches to the search specification
-sv	--header-value  Search response header values for specific matches to the search specification
```
  
### Examples of use:

Find all input fields named login on a site recursively while not leaving the root domain without case sensitivity in the match

`wwwgrep.py -t https://www.target.com -i -si “login” -rr`

Find all comments containing the term “to do” on all pages in a site 

`wwwgrep.py -t https://www.target.com -i -sc “to do” -rr`

Find all comments on a specific web page

`wwwgrep.py -t https://www.target.com/some_page -i -sc “”` 

Find all hidden fields within a list of web applications contained in the file input.txt using site recursion

`wwwgrep.py -f input.txt -sf “” -rr`
