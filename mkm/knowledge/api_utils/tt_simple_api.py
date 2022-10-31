from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json
from pprint import pprint
import requests
from time import sleep
from pathlib import Path

################################################################################

class bcolors:
    HEADER =	'\033[95m'
    OKBLUE =	'\033[94m'
    OKCYAN =	'\033[96m'
    OKGREEN =	'\033[92m'
    WARNING =	'\033[93m'
    FAIL =		'\033[91m'
    ENDC =		'\033[0m'
    BOLD =		'\033[1m'
    UNDERLINE = '\033[4m'

################################################################################

# File now contains credentials from scopus and ciencia vitae, and django secret

# Load configuration
def load_config():
	p = Path(__file__).with_name('config.json')
	con_file = open(p)
	config = json.load(con_file)
	con_file.close()
	return config

# CIENCIA VITAE

def ciencia_author(person_id):

	config = load_config()

	headers = {
		"accept": "application/json",
		"authorization": config['authorization']
	}

	params = {
			'lang': 'EN',
		}

	output_types = {
		"journal-article": True,
		"journal-issue": True,
		"book": True,
		"edited-book": True,
		"book-chapter": True,
		"book-review": True,
		"translation": True,
		"dissertation": True,
		"newspapper-article": True,
		"newsletter-article": True,
		"encyclopedia-entry": True,
		"magazine-article": True,
		"dictionary-entry": True,
		"report": True,
		"working-paper": True,
		"manual": True,
		"online-resource": True,
		"test": True,
		"website": True,
		"conference-paper": True,
		"conference-abstract": True,
		"conference-poster": True,
		"exhibition-catalogue": True,
		"preface-postface": True,
		"artistic-exhibition": True,
		"audio-recording": True,
		"musical-composition": True,
		"musical-performance": True,
		"radio-tv-program": True,
		"script": True,
		"short-fiction": True,
		"theatric": True,
		"video-recording": True,
		"visual-artwork": True,
		"sound-design": True,
		"set-design": True,
		"light-design": True,
		"choreography": True,
		"curatorial-museum-exhibition": True,
		"performance-art": True,
		"patent": True,
		"license": True,
		"disclosure": True,
		"registered-copyright": True,
		"trademark": True,
		"standard-or-policy": True,
		"invention": True,
		"data-set": True,
		"litigation": True,
		"research-technique": True,
		"spin-off-company": True,
		"technical-standard": True,
		"other-output": True,
	}

	# PERSON INFO

	is_bad = False

	#print("fetching", person_id)

	url = "https://api.cienciavitae.pt/v1.1/curriculum/"+person_id
	response = requests.get(url, headers=headers, params=params)
	#pprint(response.json())
	sleep(0.51) # max 2 requests/second

	#print(person_id)

	# ID
	#print("\n{:14s} | ".format(str(person_id)), end='')

	# NAME
	try:
		name = response.json()["identifying-info"]["person-info"]["full-name"]

		#if len(name) > 20:
		#	print("{:17s}... | ".format(str(name)[:17]), end='')
		#else:
		#	print("{:20s} | ".format(str(name)[:20]), end='')
	except:
		#print(""+bcolors.FAIL+"{:20s}".format("N/A")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		return None

	# BIO
	try:
		bio = response.json()["identifying-info"]["resume"]["value"]

		#print("{:10s} | ".format(str(len(bio))), end='')
	except:
		#print(""+bcolors.FAIL+"{:10s}".format("0")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		bio = ""
	
	# DOMAINS ACTIVITY
	try:
		domains = response.json()["identifying-info"]["domains-activity"]["domain-activity"]
		d = []
		for domain in domains:
			d.append({
				'name': domain['research-classification']['value'],
				'code': domain['research-classification']['code']
			})
		domains = d

		#print("{:7s} | ".format(str(len(domains))), end='')
	except:
		#print(""+bcolors.FAIL+"{:7s}".format("0")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		domains = []
	
	# DEGREES
	try:
		degrees = response.json()["degrees"]["degree"]
		d1 = []
		for degree in degrees:
			d1.append(degree["degree-name"])
		
		#print("{:7s} | ".format(str(len(d1))), end='')
	except:
		#print(""+bcolors.FAIL+"{:7s}".format("0")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		d1 = []

	# DISTINCTIONS
	try:
		distinctions = response.json()["distinctions"]["distinction"]
		d2 = []
		for distinction in distinctions:
			d2.append(distinction["distinction-name"])
		#print("{:12s} | ".format(str(len(d2))), end='')
	except:
		#print(""+bcolors.FAIL+"{:12s}".format("0")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		d2 = []
	
	# PROJECTS
	try:
		projects = response.json()["fundings"]["funding"]
		p = []
		for project in projects:
			areas = []
			if project['research-classifications'] != None:
				for area in project['research-classifications']['research-classification']:
					areas.append({
						'name': area['value'],
						'code': area['code']
					})
			p.append({
				'name': project['project-title'],
				'desc': project['project-description'],
				'year': project['start-date']['year'],
				'areas': areas
			})
		projects = p
		#print("{:8s} | ".format(str(len(projects))), end='')
	except:
		#print(""+bcolors.FAIL+"{:8s}".format("0")+bcolors.ENDC+" | ", end='')
		#is_bad = True
		projects = []
	
	# PUBLICATIONS (PAPERS, ARTICLES, ETC...)
	author_dict = {
		'ciencia_id': person_id,
		'name': name,
		'bio': bio,
		'domains': domains,
		'degrees': d1,
		'distinctions': d2,
		'projects': projects,
		'publications': [],
	}

	if 'Content-Length' in response.headers:
		if response.headers['Content-Length'] == "0":
			
			return author_dict

	publications = []

	if response.json()["outputs"] != None:

		outputs = response.json()["outputs"]["output"]
		for output in outputs:

			o_type = output["output-type"]["value"] # debug
			
			title = None
			date = None
			keywords = []
			ciencia_id = None
			doi = None
			scopus_id = None
			authors = []

			for output_type in output_types:
				if output[output_type] != None:

					# !!!!!! USE sub_output INSTEAD OF output !!!!!!
					sub_output = output[output_type]

					# TITLE
					title_types = ['title', 'article-title', 'book-title', 'report-title', 'paper-title', 'entry-title']
					for title_type in title_types:
						if title_type in sub_output:
							title = sub_output[title_type]
							break
					
					# DATE

					date_types = ['publication-date', 'creation-date', 'completion-date', 'date-submitted', 'presentation-date', 'date', 'release-date', 'conference-date']
					for date_type in date_types:
						if date_type in sub_output and sub_output[date_type] != None:
							#pprint(sub_output)
							y = sub_output[date_type]['year']
							m = sub_output[date_type]['month']
							d = sub_output[date_type]['day']
							if y != None:
								if m == None or d == None:
									date = y + "-01-01"
								else:
									date = y + "-" + m + "-" + d
							break
					
					if 'publication-year' in sub_output:
						if sub_output['publication-year'] != None:
							date = sub_output['publication-year'] + "-01-01"

					# KEYWORDS

					if 'keywords' in sub_output and sub_output['keywords'] != None:
						if 'keyword' in sub_output['keywords']:
							for keyword in sub_output['keywords']['keyword']:
								keywords.append(keyword)
					
					# ID'S

					for identifier in sub_output['identifiers']['identifier']:
						id_type = identifier['identifier-type']['code']
						id_val = identifier['identifier']
						if id_type == 'source-work-id':
							ciencia_id = id_val
						elif id_type == 'doi':
							doi = id_val
						elif id_type == 'eid':
							scopus_id = id_val

					# AUTHORS

					if 'authors' in sub_output and sub_output['authors'] != None:
						for author in sub_output['authors']['author']:
							author_id = author['ciencia-id']
							if author_id != None:
								authors.append(author_id)

					# END

					break





			if title == None:
				#pprint(sub_output)
				#print("\t\tBAD (TITLE)", o_type)
				#input()
				continue # DISCARD THIS OUTPUT. FOR LOOP GOES TO NEXT ITERATION
			elif date == None:
				#pprint(sub_output)
				#print("\t\t\t\tBAD (DATE)", o_type)
				#input()
				continue # DISCARD THIS OUTPUT. FOR LOOP GOES TO NEXT ITERATION
			#else:
			#	print("GOOD", authors )

			pub_dict = {
				'type': o_type,
				'title': title,
				'date': date,
				'keywords': keywords,
				'ciencia_id': ciencia_id,
				'doi': doi,
				'scopus_id': scopus_id,
				'authors': authors,
			}

			publications.append(pub_dict)

			#for output_type in output_types:
			#	if output[output_type] != None and output_types[output_type]:
			#		
			#		pprint(output[output_type])

			#		print("\n" + output_type)
					
			#		print("\nPress ENTER to continue")
			#		input()

			#		output_types[output_type] = False
			#		break
	
	author_dict['publications'] = publications

	return author_dict

	#input()

#ciencia_author("6016-3F49-8427")# 9C1C-C52C-A1E2

# TEST CIENCIA FUNCTIONS
if False:

	config = load_config()

	headers = {
		"accept": "application/json",
		"authorization": config["authorization"]
	}

	# GET SOME ID's

	ids = []
	for i in range(1):

		params = {
			'order': 'Ascending',
			'pagination': 'true',
			'rows': '60',
			'page': str(i+1),
			'lang': 'EN',
		}
		url = "https://api.cienciavitae.pt/v1.1/searches/persons/all"

		response = requests.get(url, headers=headers, params=params)
		sleep(0.51) # max 2 requests/second

		for person in response.json()["result"]["person"]:
			for identification in person["author-identifiers"]["author-identifier"]:
				if (identification["identifier-type"]["code"] == "CIENCIAID"):
					ids.append(identification["identifier"])

	#print(ids)
	
	# ITERATE ID's
	#print()

	#print( ("{:14s} | {:20s} | {:10s} | {:7s} | "+ #{:9s} | 
	#	"{:7s} | {:12s} | {:8s} | {:12s} | {:11s} | {:13s} | {:6s}").format( 
	#	"CIENCIA ID", "NAME", "BIO LENGTH", "DOMAINS", #"LANGUAGES", 
	#	"DEGREES", "DISTINCTIONS", "PROJECTS", 
	#	"CONF. PAPERS", "J. ARTICLES", "BOOK CHAPTERS", "OTHERS" ), end='' )

	bad_ids = ['EB1A-12B1-5160', '3E19-DFAF-F6F0', '9C10-38A2-0F19', 'DB13-AB9D-7C3E', '0B13-BA1E-678C', 'DA1C-ED3A-32A8', '211A-67A1-9B0F', '8510-3206-647D', 'BE17-1440-9F89', 'ED12-27EA-EFAC', 'C31F-D198-BC55', 'C317-6E65-CFF3', '021E-079C-C4B8', '2318-970D-EF59', '6017-A852-BA36', '7812-B995-C3BF', '6A18-DDD4-1291', '1B1F-31CD-D58D', 'D716-1FD4-F5CA', 'C715-1E14-0978', '2C17-BC9D-32EA', 'DC1D-0C4C-116B', '9E11-2CAB-AA45', '7A15-C663-895A', '1F17-1938-0683', '461C-1810-70F6', 'D712-0376-1510', 'F714-6214-C2C0', 'CF13-24DD-1E35', '4918-417A-8700', 'B313-518C-ADCA', 'C010-B357-7CFA', 'AF1A-C7D3-B993', '6B12-175A-697D', '1510-B44A-74E7', '6D1A-7554-A0C6', '731F-7686-397B', 'EB1A-E96F-2774', 'B117-42AE-8342', '2A13-632C-D743', '9715-A1A9-4C25', '1711-45CC-C3E0', '7F1D-FBEE-D79F', '4E16-2027-CC09', 'AF1A-BC9D-C865', 'C41D-838C-1866', '5713-9AE1-8CFC', '1019-2EC9-876A', 'A01C-A7CE-FCFC', '5310-9FCB-BABF', '171B-5D54-78F1', '6214-D131-C470', 'BD1E-E067-CC7C', '1D17-89D5-91E8', 'AF1B-8D21-A7AF', '9D13-3B26-5CF2', '0C1F-9648-2A48', '341D-EB51-5D7B', 'A61A-1279-0C28', 'A519-3309-A0F4', '9B1B-C73E-BEF5', 'AB1C-1F7A-8061', 'CC11-FFEF-E306', '251D-C2C6-0613', 'E01E-157E-2615', '1B1E-1C65-53C7', 'A616-B355-54AB', 'CB11-C701-4719', '8A1E-A268-BAF0', 'C316-1738-8504', '4B1D-A69F-59F6', '4F1D-23BD-1189', 'A81A-D410-93F2', '1312-81AC-04CB', 'A513-DF06-CB8B', '5E10-ACD3-D870', 'BD11-7AA3-4E92', '9217-B241-D205', '3311-9B4F-0978', 'BD1F-83D3-73C2', '6614-C5AE-3CF7', '6B1B-661F-8F83', 'BD18-04CD-4A48', '2811-48A8-49E0', '2E12-880D-02DE', '3615-166F-3551', 'B413-33A9-D710', 'F715-FE76-5CA0', 'B610-D2D6-DB0F', '9F18-6CC1-6E5A', 'FE1F-ACA0-C553', '6811-A987-CB31', 'B718-1FC8-42C5', 'AC1F-2790-F037', 'FD14-1E99-E478', '9712-0D6D-AA4E', 'DD17-1CFC-6023', '7F19-794C-DB61', '7816-2154-B0B4', '2417-871C-1A61', 'F01B-975A-258B', '8B13-CBD2-86DD', '4A13-5837-81B8', '421C-4281-6C6B', '7618-0703-03FC', '3D1F-4AA5-FC35', 'EB1F-4DB2-B0C9', 'F616-FB28-6B48', 'DF1A-C053-D14F', '801B-469F-3CFC', '7217-4695-1E9A', 'D816-F928-EFD7', 'B91C-5F00-CE05', 'AB1D-4002-BCBB', '2A15-C063-717A', 'E415-E21D-D78A', 'D615-9319-DD7C', '8F1F-B61B-1692', 'F31A-8616-5B83', '5C10-0155-3858', 'F518-C66E-F5B7', '2518-778C-4EC6', '331B-D565-A6E3', 'B31F-510F-CD10', '351F-3169-F1A0', '6F16-6EAB-67B6', '1B19-28F5-DE1F', 'AD17-E4C5-322D', '7D16-6889-820F', 'B71F-C386-CDAC', 'BB10-F950-234D', 'E21F-2E7B-91BA', 'D118-9316-97F2', '9A1E-30E5-F8C0', 'DB14-4CB9-255D', 'C71B-5544-F8B4']

	for person_id in ids:

		if person_id not in bad_ids:

			print(person_id, end=' ')
			#pprint(ciencia_author(person_id))

#print()

# SCOPUS

## Initialize author search object and execute search
#auth_srch = ElsSearch('authlast(Neves) and authfirst(António J.R.)','author')
#auth_srch.execute(client)
#print ("auth_srch has", len(auth_srch.results), "results.")
#print ("results", auth_srch.results)

def scopus_author(author_id):
	config = load_config()
	## Initialize client
	client = ElsClient(config['apikey'])
	client.inst_token = config['insttoken']

	## Author example
	# Initialize author with uri
	my_auth = ElsAuthor(uri = 'https://api.elsevier.com/content/author/author_id/' + str(author_id))
	
	if my_auth.read(client):

		### AUTHOR ###

		author_name = my_auth.full_name
		author_scopus_id = my_auth._data['coredata']['dc:identifier'].split(':')[1]
		author_orcid_id = my_auth._data['coredata']['orcid']

		author_name_list = []
		if 'name-variant' in my_auth._data['author-profile']:

			name_variant = my_auth._data['author-profile']['name-variant']
			if isinstance(name_variant, list):
				for variant in name_variant:
					author_name_list.append("{} {}".format(variant['given-name'], variant['surname']))
			else:
				author_name_list.append("{} {}".format(name_variant['given-name'], name_variant['surname']))
		
		#print("\n-----------------------------------------------")
		#print(bcolors.OKGREEN + "\nAuthor:" , 		my_auth.full_name, bcolors.ENDC)
		#print("    Scopus ID:", author_scopus_id  )
		#print("    ORCID ID:",  author_orcid_id  )
		#if 'name-variant' in my_auth._data['author-profile']:
		#	print("    Name Variants:",	len(author_name_list)  )


		### AFFILIATION ### ### STRUCTURE ###

		author_current_affiliation_list = []

		affiliation = my_auth._data['author-profile']['affiliation-current']['affiliation']
		if isinstance(affiliation, list):
			#print("\nCurrent Affiliations:")
			for a in affiliation:
				affiliation_name = a['ip-doc']['afdispname']
				affiliation_id = a['ip-doc']['@id']
				if '@parent' in a:
					affiliation_parent = a['@parent']
				else:
					affiliation_parent = None
				#print("   ", affiliation_name  )
				#print("    Scopus ID:", affiliation_id  )

				affiliation_dict = {
					'affiliation_name': affiliation_name,
					'affiliation_id': affiliation_id,
					'affiliation_parent': affiliation_parent
				}
				author_current_affiliation_list.append(affiliation_dict)
		else:
			affiliation_name = affiliation['ip-doc']['afdispname']
			affiliation_id = affiliation['ip-doc']['@id']
			if '@parent' in affiliation:
				affiliation_parent = affiliation['@parent']
			else:
				affiliation_parent = None
			#print("\n    Current Affiliation:", affiliation_name  )
			#print("        Scopus ID:", affiliation_id  )

			affiliation_dict = {
				'affiliation_name': affiliation_name,
				'affiliation_id': affiliation_id,
				'affiliation_parent': affiliation_parent
			}
			author_current_affiliation_list.append(affiliation_dict)

		author_previous_affiliation_list = []
		for prev_affiliation in my_auth._data['author-profile']['affiliation-history']['affiliation']:
			if not isinstance(prev_affiliation, dict) or not 'afdispname' in prev_affiliation['ip-doc']:
				continue
			affiliation_name = prev_affiliation['ip-doc']['afdispname']
			affiliation_id = prev_affiliation['@affiliation-id']
			if '@parent' in prev_affiliation:
				affiliation_parent = prev_affiliation['@parent']
			else:
				affiliation_parent = None

			affiliation_dict = {
				'affiliation_name': affiliation_name,
				'affiliation_id': affiliation_id,
				'affiliation_parent': affiliation_parent
			}
			author_previous_affiliation_list.append(affiliation_dict)

		#print("        Affiliation History:",	len(author_previous_affiliation_list)  )



		### ETC ###

		author_document_count = my_auth._data['coredata']['document-count']
		author_citation_count = my_auth._data['coredata']['citation-count']
		author_cited_by_count = my_auth._data['coredata']['cited-by-count']

		#print("\n    Document Count:", author_document_count)
		#print("    Citation Count:", author_citation_count)
		#print("    Cited-By Count:", author_cited_by_count)

		author_areas = []

		for area in my_auth._data['subject-areas']['subject-area']:
			area_name = area['$']
			area_abbreviation = area['@abbrev']
			area_code = area['@code']

			area_dict = {
				'area_name': area_name,
				'area_abbreviation': area_abbreviation,
				'area_code': area_code
			}
			author_areas.append(area_dict)

		#print("\n    Areas:",        	len(author_areas) , "[ ", end='' )
		#i = 0
		#for area in author_areas:
		#	if i < 3:
		#		print(area['area_name'], ", ", end='')
		#	else:
		#		print("... ]")
		#		break
		#	i += 1
		
		#my_auth.write()

		author_dict = {
			'author_name': author_name,
			'author_scopus_id': author_scopus_id,
			'author_orcid_id': author_orcid_id,
			'author_name_list': author_name_list,
			'author_current_affiliation_list': author_current_affiliation_list,
			'author_previous_affiliation_list': author_previous_affiliation_list,
			'author_document_count': author_document_count,
			'author_citation_count': author_citation_count,
			'author_cited_by_count': author_cited_by_count,
			'author_areas': author_areas
		}

		return author_dict

def scopus_author_docs(author_id, author_pk):
	config = load_config()
	## Initialize client
	client = ElsClient(config['apikey'])
	client.inst_token = config['insttoken']

	## Author example
	# Initialize author with uri
	my_auth = ElsAuthor(uri = 'https://api.elsevier.com/content/author/author_id/' + str(author_id))
	
	docs = []

	if my_auth.read(client):

		### SEARCH DOCS ###
		
		## Initialize doc search object using Scopus and execute search, retrieving 
		#   all results
		doc_srch = ElsSearch("AU-ID("+str(author_id)+")",'scopus')
		doc_srch.execute(client, get_all = True)
		#print ("\ndoc_srch has", len(doc_srch.results), "results.\n")

		doc_ids = ['85044949656', '85063456029', '85063028413', '85048212515', '85086630979', '85087658242', '85098456035', '85100446723', '85020429778', '84990232272', '85086630979', '85100446723', '33646866379', '79952617090', '79952628276']

		

		for doc in doc_srch.results:
		#if len(doc_srch.results) != 0:
		#	doc = doc_srch.results[0]

			doc_title = doc['dc:title']
			doc_scopus_id = doc['dc:identifier'].split(':')[-1]

			#if doc_scopus_id in doc_ids:

			#print(bcolors.OKCYAN + "Document:", doc_title, bcolors.ENDC )
			#print( "    Scopus ID:", doc_scopus_id )

			if 'prism:doi' in doc:
				doc_doi = doc['prism:doi']
				#print( "    DOI (Document Object Identifier):", doc_doi )
			else:
				doc_doi = None

			doc_eid = doc['eid']
			doc_date = doc['prism:coverDate']
			doc_type = doc['subtypeDescription']

			#print( "    EID (Electronic ID):", doc_eid )
			#print( "    Date:", doc_date)
			#print( "    Type:", doc_type)

			## Scopus (Abtract) document example
			# Initialize document with ID as integer
			scp_doc = AbsDoc(scp_id = doc_scopus_id)

			doc_areas = []
			doc_keywords = []

			if scp_doc.read(client):
				#print()
				#pprint(vars(scp_doc))

				#print("scp_doc.title: ", scp_doc.title)
				
				try:
					for area in scp_doc._data['subject-areas']['subject-area']:
						area_name = area['$']
						area_abbreviation = area['@abbrev']
						area_code = area['@code']

						area_dict = {
							'area_name': area_name,
							'area_abbreviation': area_abbreviation,
							'area_code': area_code
						}
						doc_areas.append(area_dict)

					#print( "    Areas:", len(doc_areas), end=' ' )
					#print(doc_areas)
				except:
					pass

				try:
					#print( "    Keywords:", len(scp_doc._data['idxterms']['mainterm']), end=' ' )
					
					for keyword in scp_doc._data['idxterms']['mainterm']:
						doc_keywords.append(keyword['$'])
					#print(doc_keywords)
				except:
					pass

				doc_abstract = scp_doc._data['item']['bibrecord']['head']['abstracts']
				#print(len(doc_abstract))

				#print( doc_abstract )

				#scp_doc.write()

			# Assume true until error
			available = True
			clean_text = ""

			if 'prism:doi' in doc:
				## ScienceDirect (full-text) document example using DOI
				doi_doc = FullDoc(doi = doc_doi)
				#print()
				if doi_doc.read(client):
					#print("    Full Text Available")
					#print ("doi_doc.title: ", doi_doc.title)

					# ORIGINAL TEXT WITH IMAGE LINKS AND OTHER 'TRASH'
					original_text = doi_doc._data['originalText']

					if isinstance(original_text, str):

						# SPLIT ALL WORDS INTO ARRAY
						original_text_split = original_text.split(" ")

						# INITIALIZE CLEAN TEXT
						#clean_text = "" # already done outside
						bad_words = [':/', 'sml', 'jpg', '-s2', 'pdf', 'gif', 'png', 'svg', 'ALTIMG', 'IMAGE-DOWNSAMPLED', 'IMAGE-THUMBNAIL', 'IMAGE-HIGH-RES', 'AAM-PDF', 'AAM-PAGE-IMAGE']
						for word in original_text_split:
							clean = True # Assume word is clean until we find a bad expression
							for expression in bad_words:
								#print(expression, "in", word, expression in word)
								if expression in word:
									clean = False
									break # Found a bad expression. "next word please!"
							if clean:
								clean_text += word + " "
						# SPLIT CLEAN TEXT (for visually checking against original)
						#clean_text_split = clean_text.split(" ")
						
						# CREATE AN "ORIGINAL" TEXT WITH THE CLEAN WORDS HIGHLIGHTED
						#overlap_text = ""
						#for word in original_text_split:
						#	if word in clean_text_split:
						#		word = bcolors.ENDC + word + bcolors.FAIL
						#	overlap_text += word + " "
							
						#print(clean_text)

						#print ( "TEXT:", bcolors.FAIL + overlap_text + bcolors.ENDC )
						#print("\nPress ENTER to continue")
						#input()

						#print(vars(doi_doc))
						#doi_doc.write()

					else:
						available = False

				else:
					#print(bcolors.FAIL + "    Read text failed" + bcolors.ENDC)
					available = False
			else:
				#print(bcolors.FAIL + "    No 'DOI' available" + bcolors.ENDC)
				#print('doc_eid', doc_eid)
				available = False
			
			#print()

			doc_dict = {
				'doc_title': doc_title,
				'doc_scopus_id': doc_scopus_id,
				'doc_doi': doc_doi,
				'doc_eid': doc_eid,
				'doc_date': doc_date,
				'doc_type': doc_type,
				'doc_areas': doc_areas,
				'doc_keywords': doc_keywords,
				'doc_abstract': doc_abstract,
				'available': available,
				'clean_text': clean_text
			}

			docs.append(doc_dict)

	with open('difflists/'+str(author_pk)+'.json', 'w', encoding='utf-8') as f:
		json.dump(docs, f, ensure_ascii=False, indent=4)
	return docs

# TEST SCOPUS FUNCTIONS

if False:
	# TEST ID'S
	ids = ['43461712600', '57188881218', '57203431176', '57199578161', '49361962700', '54987996200']
	for id in ids:
		pprint(scopus_author(id))
		pprint(scopus_author_docs(id))

################################################################################

# SCOPUS TUTORIAL CODE

if False:

	## Author example
	# Initialize author with uri
	my_auth = ElsAuthor(
			uri = 'https://api.elsevier.com/content/author/author_id/7004367821')
	# Read author data, then write to disk
	if my_auth.read(client):
		print ("my_auth.full_name: ", my_auth.full_name)
		my_auth.write()
	else:
		print ("Read author failed.")

	## Affiliation example
	# Initialize affiliation with ID as string
	my_aff = ElsAffil(affil_id = '60101411')
	if my_aff.read(client):
		print ("my_aff.name: ", my_aff.name)
		my_aff.write()
	else:
		print ("Read affiliation failed.")

	## Scopus (Abtract) document example
	# Initialize document with ID as integer
	scp_doc = AbsDoc(scp_id = 84872135457)
	if scp_doc.read(client):
		print ("scp_doc.title: ", scp_doc.title)
		scp_doc.write()   
	else:
		print ("Read document failed.")

	## ScienceDirect (full-text) document example using PII
	pii_doc = FullDoc(sd_pii = 'S1674927814000082')
	if pii_doc.read(client):
		print ("pii_doc.title: ", pii_doc.title)
		pii_doc.write()   
	else:
		print ("Read document failed.")

	## ScienceDirect (full-text) document example using DOI
	doi_doc = FullDoc(doi = '10.1016/S1525-1578(10)60571-5')
	if doi_doc.read(client):
		print ("doi_doc.title: ", doi_doc.title)
		doi_doc.write()   
	else:
		print ("Read document failed.")


	## Load list of documents from the API into affilation and author objects.
	# Since a document list is retrieved for 25 entries at a time, this is
	#  a potentially lenghty operation - hence the prompt.
	print ("Load documents (Y/N)?")
	s = input('--> ')

	if (s == "y" or s == "Y"):

		## Read all documents for example author, then write to disk
		if my_auth.read_docs(client):
			print ("my_auth.doc_list has " + str(len(my_auth.doc_list)) + " items.")
			my_auth.write_docs()
		else:
			print ("Read docs for author failed.")

		## Read all documents for example affiliation, then write to disk
		if my_aff.read_docs(client):
			print ("my_aff.doc_list has " + str(len(my_aff.doc_list)) + " items.")
			my_aff.write_docs()
		else:
			print ("Read docs for affiliation failed.")

	## Initialize author search object and execute search
	auth_srch = ElsSearch('authlast(keuskamp)','author')
	auth_srch.execute(client)
	print ("auth_srch has", len(auth_srch.results), "results.")

	## Initialize affiliation search object and execute search
	aff_srch = ElsSearch('affil(amsterdam)','affiliation')
	aff_srch.execute(client)
	print ("aff_srch has", len(aff_srch.results), "results.")

	## Initialize doc search object using Scopus and execute search, retrieving 
	#   all results
	doc_srch = ElsSearch("AFFIL(dartmouth) AND AUTHOR-NAME(lewis) AND PUBYEAR > 2011",'scopus')
	doc_srch.execute(client, get_all = True)
	print ("doc_srch has", len(doc_srch.results), "results.")

	## Initialize doc search object using ScienceDirect and execute search, 
	#   retrieving all results
	doc_srch = ElsSearch("star trek vs star wars",'sciencedirect')
	doc_srch.execute(client, get_all = False)
	print ("doc_srch has", len(doc_srch.results), "results.")

#print()
