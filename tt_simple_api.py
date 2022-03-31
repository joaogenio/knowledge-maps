from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json

from pprint import pprint

import requests

from time import sleep

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

class Author:						# EXAMPLES // DESCRIPTION
	def __init__(self,				
		name,						# António J.R. Neves
		scopus_id,					# 43461712600
		orcid_id,					# 0000-0001-5433-6667
		name_list,					# ['A.J.R.', 'A. Neves', ...]

									# Following 3 fields should become relations
									# in a proper database scenario

		current_affiliation_list,	# [Affiliation(name='Universidade de Aveiro'
									# , ...), ...]
									# // Not sure if affiliation history has to
									# // include the current affiliations

		affiliation_history_list,	# [Affiliation(name='Universidade de Aveiro'
									#, ...), ...]

		document_list,				# [Document(...), ...]

		citation_count,				# 
		cited_by_count,				# Author cited by n documents

		area_freq,					# {Area(name='Artificial Intelligence'): 10}
									# // Areas and the amount of times they
									# // appeared in the author's documents

		# CIENCIA VITAE fields
		bio							# Author biography

		# TO DO'S

		# PEER REVIEWS
		# COURSES TAUGHT
		# ACTUATION DOMAINS
		#
		# PROJECTS
		
		
		
		):
		self.name = name
		self.scopus_id = scopus_id
		self.orcid_id = orcid_id
		self.name_list = name_list
		self.current_affiliation_list = current_affiliation_list
		self.affiliation_history_list = affiliation_history_list
		self.document_list = document_list
		self.citation_count = citation_count
		self.cited_by_count = cited_by_count
		self.area_freq = area_freq
		self.bio = bio

class Affiliation:					# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Universidade de Aveiro
		scopus_id):					# 60024825
		self.name = name
		self.scopus_id = scopus_id

class Area:							# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Software
		abbreviation,				# COMP // Can be the same for many areas
		code):						# 1712
		self.name = name
		self.abbreviation = abbreviation
		self.code = code

class Document:						# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Creating a Project track in a 5-year
									# integrated Engineering Curricullum
		scopus_id,					# 85124808238
		doi,						# 10.1109/WEEF/GEDC53299.2021.9657160
		eid,						# 2-s2.0-85124808238
		date,						# 2021-01-01
		d_type,						# Conference Paper
		area_list,					# [Area(), ...]
		keyword_list,				# ['Active Learning', 'Soft skills', ...]
		full_text					# // Full document text
		):
		self.name = name
		self.scopus_id = scopus_id
		self.doi = doi
		self.eid = eid
		self.date = date
		self.d_type = d_type
		self.area_list = area_list
		self.keyword_list = keyword_list
		self.full_text = full_text

################################################################################

# Code from scoups example
# File now contains scopus and ciencia vitae credentials

## Load configuration
con_file = open("config.json")
config = json.load(con_file)
con_file.close()

# CIENCIA VITAE

headers = {
	"accept": "application/json",
	"authorization": config['authorization']
}

if True:

	# GET SOME ID's

	ids = []
	for i in range(3):
		url = "https://qa.cienciavitae.pt/api/v1.1/searches/persons/all?order=Ascending&pagination=true&rows=60&page="+str(i+1)+"&lang=EN"
		response = requests.get(url, headers=headers)
		sleep(0.51) # max 2 requests/second
		#print(response.json())
		for person in response.json()["result"]["person"]:
			for identification in person["author-identifiers"]["author-identifier"]:
				if (identification["identifier-type"]["code"] == "CIENCIAID"):
					ids.append(identification["identifier"])

	#print(ids)
	
	# ITERATE ID's
	print()

	print( ("{:14s} | {:20s} | {:10s} | {:7s} | "+ #{:9s} | 
		"{:7s} | {:12s} | {:8s} | {:12s} | {:11s} | {:13s} | {:6s}").format( 
		"CIENCIA ID", "NAME", "BIO LENGTH", "DOMAINS", #"LANGUAGES", 
		"DEGREES", "DISTINCTIONS", "PROJECTS", 
		"CONF. PAPERS", "J. ARTICLES", "BOOK CHAPTERS", "OTHERS" ), end='' )

	bad_ids = ['EB1A-12B1-5160', '3E19-DFAF-F6F0', '9C10-38A2-0F19', 'DB13-AB9D-7C3E', '0B13-BA1E-678C', 'DA1C-ED3A-32A8', '211A-67A1-9B0F', '8510-3206-647D', 'BE17-1440-9F89', 'ED12-27EA-EFAC', 'C31F-D198-BC55', 'C317-6E65-CFF3', '021E-079C-C4B8', '2318-970D-EF59', '6017-A852-BA36', '7812-B995-C3BF', '6A18-DDD4-1291', '1B1F-31CD-D58D', 'D716-1FD4-F5CA', 'C715-1E14-0978', '2C17-BC9D-32EA', 'DC1D-0C4C-116B', '9E11-2CAB-AA45', '7A15-C663-895A', '1F17-1938-0683', '461C-1810-70F6', 'D712-0376-1510', 'F714-6214-C2C0', 'CF13-24DD-1E35', '4918-417A-8700', 'B313-518C-ADCA', 'C010-B357-7CFA', 'AF1A-C7D3-B993', '6B12-175A-697D', '1510-B44A-74E7', '6D1A-7554-A0C6', '731F-7686-397B', 'EB1A-E96F-2774', 'B117-42AE-8342', '2A13-632C-D743', '9715-A1A9-4C25', '1711-45CC-C3E0', '7F1D-FBEE-D79F', '4E16-2027-CC09', 'AF1A-BC9D-C865', 'C41D-838C-1866', '5713-9AE1-8CFC', '1019-2EC9-876A', 'A01C-A7CE-FCFC', '5310-9FCB-BABF', '171B-5D54-78F1', '6214-D131-C470', 'BD1E-E067-CC7C', '1D17-89D5-91E8', 'AF1B-8D21-A7AF', '9D13-3B26-5CF2', '0C1F-9648-2A48', '341D-EB51-5D7B', 'A61A-1279-0C28', 'A519-3309-A0F4', '9B1B-C73E-BEF5', 'AB1C-1F7A-8061', 'CC11-FFEF-E306', '251D-C2C6-0613', 'E01E-157E-2615', '1B1E-1C65-53C7', 'A616-B355-54AB', 'CB11-C701-4719', '8A1E-A268-BAF0', 'C316-1738-8504', '4B1D-A69F-59F6', '4F1D-23BD-1189', 'A81A-D410-93F2', '1312-81AC-04CB', 'A513-DF06-CB8B', '5E10-ACD3-D870', 'BD11-7AA3-4E92', '9217-B241-D205', '3311-9B4F-0978', 'BD1F-83D3-73C2', '6614-C5AE-3CF7', '6B1B-661F-8F83', 'BD18-04CD-4A48', '2811-48A8-49E0', '2E12-880D-02DE', '3615-166F-3551', 'B413-33A9-D710', 'F715-FE76-5CA0', 'B610-D2D6-DB0F', '9F18-6CC1-6E5A', 'FE1F-ACA0-C553', '6811-A987-CB31', 'B718-1FC8-42C5', 'AC1F-2790-F037', 'FD14-1E99-E478', '9712-0D6D-AA4E', 'DD17-1CFC-6023', '7F19-794C-DB61', '7816-2154-B0B4', '2417-871C-1A61', 'F01B-975A-258B', '8B13-CBD2-86DD', '4A13-5837-81B8', '421C-4281-6C6B', '7618-0703-03FC', '3D1F-4AA5-FC35', 'EB1F-4DB2-B0C9', 'F616-FB28-6B48', 'DF1A-C053-D14F', '801B-469F-3CFC', '7217-4695-1E9A', 'D816-F928-EFD7', 'B91C-5F00-CE05', 'AB1D-4002-BCBB', '2A15-C063-717A', 'E415-E21D-D78A', 'D615-9319-DD7C', '8F1F-B61B-1692', 'F31A-8616-5B83', '5C10-0155-3858', 'F518-C66E-F5B7', '2518-778C-4EC6', '331B-D565-A6E3', 'B31F-510F-CD10', '351F-3169-F1A0', '6F16-6EAB-67B6', '1B19-28F5-DE1F', 'AD17-E4C5-322D', '7D16-6889-820F', 'B71F-C386-CDAC', 'BB10-F950-234D', 'E21F-2E7B-91BA', 'D118-9316-97F2', '9A1E-30E5-F8C0', 'DB14-4CB9-255D', 'C71B-5544-F8B4']

	for person_id in ids:

		if person_id not in bad_ids:

			# PERSON INFO

			is_bad = False

			url = "https://qa.cienciavitae.pt/api/v1.1/curriculum/"+person_id+"/identifying-info?lang=EN"
			response = requests.get(url, headers=headers)
			sleep(0.51) # max 2 requests/second

			#print(person_id)

			# ID
			print("\n{:14s} | ".format(str(person_id)), end='')

			# NAME
			try:
				name = response.json()["person-info"]["full-name"]
				if len(name) > 20:
					print("{:17s}... | ".format(str(name)[:17]), end='')
				else:
					print("{:20s} | ".format(str(name)[:20]), end='')
			except:
				print(""+bcolors.FAIL+"{:20s}".format("N/A")+bcolors.ENDC+" | ", end='')
				is_bad = True

			# BIO
			try:
				bio = response.json()["resume"]["value"]
				print("{:10s} | ".format(str(len(bio))), end='')
			except:
				print(""+bcolors.FAIL+"{:10s}".format("0")+bcolors.ENDC+" | ", end='')
				is_bad = True
			
			# DOMAINS ACTIVITY
			try:
				domains = response.json()["domains-activity"]["domain-activity"]
				print("{:7s} | ".format(str(len(domains))), end='')
			except:
				print(""+bcolors.FAIL+"{:7s}".format("0")+bcolors.ENDC+" | ", end='')
				is_bad = True
			
			# LANGUAGES
			#try:
			#	langs = response.json()["language-competencies"]["language-competency"]
			#	print("{:9s} | ".format(str(len(langs))), end='')
			#except:
			#	print(""+bcolors.FAIL+"{:9s}".format("0")+bcolors.ENDC+" | ", end='')
			#	is_bad = True
			
			# DEGREES
			try:
				url = "https://qa.cienciavitae.pt/api/v1.1/curriculum/"+person_id+"/degree?lang=EN"
				response = requests.get(url, headers=headers)
				sleep(0.51) # max 2 requests/second
				degrees = response.json()["degree"]
				d = []
				for degree in degrees:
					d.append(degree["degree-name"])
				print("{:7s} | ".format(str(len(d))), end='')
			except:
				print(""+bcolors.FAIL+"{:7s}".format("0")+bcolors.ENDC+" | ", end='')
				is_bad = True
			
			# DISTINCTIONS
			try:
				url = "https://qa.cienciavitae.pt/api/v1.1/curriculum/"+person_id+"/distinction?lang=EN"
				response = requests.get(url, headers=headers)
				sleep(0.51) # max 2 requests/second
				distinctions = response.json()["distinction"]
				d = []
				for distinction in distinctions:
					d.append(distinction["distinction-name"])
				print("{:12s} | ".format(str(len(d))), end='')
			except:
				print(""+bcolors.FAIL+"{:12s}".format("0")+bcolors.ENDC+" | ", end='')
				#is_bad = True
			
			# PROJECTS
			try:
				url = "https://qa.cienciavitae.pt/api/v1.1/curriculum/"+person_id+"/funding?lang=EN"
				response = requests.get(url, headers=headers)
				sleep(0.51) # max 2 requests/second
				projects = response.json()["funding"]
				print("{:8s} | ".format(str(len(projects))), end='')
			except:
				print(""+bcolors.FAIL+"{:8s}".format("0")+bcolors.ENDC+" | ", end='')
				#is_bad = True
			
			# PUBLICATIONS (PAPERS, ARTICLES, ETC...)
			try:
				url = "https://qa.cienciavitae.pt/api/v1.1/curriculum/"+person_id+"/output?lang=EN"
				response = requests.get(url, headers=headers)
				sleep(0.51) # max 2 requests/second
				outputs = response.json()["output"]

				papers = 0
				articles = 0
				chapters = 0
				others = 0
				for output in outputs:
					o_type = output["output-type"]["value"]
					if o_type == "Conference paper":
						papers += 1
					elif o_type == "Journal article":
						articles += 1
					elif o_type == "Book chapter":
						chapters += 1
					else:
						others += 1
				
				if papers > 0: print("{:12s} | ".format( str(papers) ), end='')
				else: print(""+bcolors.FAIL+"{:12s}".format("0")+bcolors.ENDC+" | ", end='')
				if articles > 0: print("{:11s} | ".format( str(articles) ), end='')
				else: print(""+bcolors.FAIL+"{:11s}".format("0")+bcolors.ENDC+" | ", end='')
				if chapters > 0: print("{:13s} | ".format( str(chapters) ), end='')
				else: print(""+bcolors.FAIL+"{:13s}".format("0")+bcolors.ENDC+" | ", end='')
				if others > 0: print("{:6s}".format( str(others) ), end='')
				else: print(""+bcolors.FAIL+"{:6s}".format("0")+bcolors.ENDC+"", end='')

				
				#print("{:12s} | {:11s} | {:13s} | {:6s}".format( str(papers), str(articles), str(chapters), str(others) ), end='')
			except:
				print(""+bcolors.FAIL+"{:12s}".format("0")+bcolors.ENDC+
					" | "+bcolors.FAIL+"{:11s}".format("0")+bcolors.ENDC+
					" | "+bcolors.FAIL+"{:13s}".format("0")+bcolors.ENDC+
					" | "+bcolors.FAIL+"{:6s}".format("0")+bcolors.ENDC, end='')
				#is_bad = True
			
			if is_bad:
				bad_ids.append(person_id)
	
	#print(bad_ids)

print()

# SCOPUS

if False:

	## Load configuration
	## *moved

	## Initialize client
	client = ElsClient(config['apikey'])
	client.inst_token = config['insttoken']




	## Initialize author search object and execute search
	#auth_srch = ElsSearch('authlast(Neves) and authfirst(António J.R.)','author')
	#auth_srch.execute(client)
	#print ("auth_srch has", len(auth_srch.results), "results.")
	#print ("results", auth_srch.results)



	ids = ['43461712600']#, '57188881218', '57203431176', '57199578161', '49361962700', '54987996200']

	for author_id in ids:

		## Author example
		# Initialize author with uri
		my_auth = ElsAuthor(
				uri = 'https://api.elsevier.com/content/author/author_id/' + author_id)
		# Read author data, then write to disk
		if my_auth.read(client):

			#pprint(vars(my_auth))



			### AUTHOR ###

			author_name = my_auth.full_name
			author_scopus_id = 		my_auth._data['coredata']['dc:identifier'].split(':')[1]
			author_orcid_id = my_auth._data['coredata']['orcid']

			author_name_list = []
			if 'name-variant' in my_auth._data['author-profile']:
				for variant in my_auth._data['author-profile']:
					author_name_list.append(variant)
			


			print("\n-----------------------------------------------")
			print(bcolors.OKGREEN + "\nAuthor:" , 		my_auth.full_name, bcolors.ENDC)
			print("    Scopus ID:", author_scopus_id  )
			print("    ORCID ID:",  my_auth._data['coredata']['orcid']  )
			if 'name-variant' in my_auth._data['author-profile']:
				print("    Name Variants:",	len(my_auth._data['author-profile']['name-variant'])  )



			### AFFILIATION ### ### STRUCTURE ###

			author_current_affiliation_list = []

			affiliation = my_auth._data['author-profile']['affiliation-current']['affiliation']
			if isinstance(affiliation, list):
				print("\nCurrent Affiliations:")
				for a in affiliation:
					print("   ", a['ip-doc']['afdispname']  )
					print("    Scopus ID:", a['ip-doc']['@id']  )
			else:
				print("\n    Current Affiliation:", affiliation['ip-doc']['afdispname']  )
				print("        Scopus ID:", affiliation['ip-doc']['@id']  )

			print("        Affiliation History:",	len(my_auth._data['affiliation-history']['affiliation'])  )



			### ETC ###

			print("\n    Document Count:",	my_auth._data['coredata']['document-count']  )
			print("    Citation Count:",    my_auth._data['coredata']['citation-count']  )
			print("    Cited-By Count:",    my_auth._data['coredata']['cited-by-count']  )

			print("\n    Areas:",        	len(my_auth._data['subject-areas']['subject-area']) , "[ ", end='' )
			i = 0
			for area in my_auth._data['subject-areas']['subject-area']:
				if i < 3:
					print(area['$'], ", ", end='')
				else:
					print("... ]")
					break
				i += 1
			
			my_auth.write()



			### SEARCH DOCS ###
			
			## Initialize doc search object using Scopus and execute search, retrieving 
			#   all results
			doc_srch = ElsSearch("AU-ID("+author_scopus_id+")",'scopus')
			doc_srch.execute(client, get_all = True)
			print ("\ndoc_srch has", len(doc_srch.results), "results.\n")

			#for doc in doc_srch.results:
			if len(doc_srch.results) != 0:
				doc = doc_srch.results[0]

				print(bcolors.OKCYAN + "Document:", doc['dc:title'], bcolors.ENDC )
				doc_scopus_id = doc['dc:identifier']
				print( "    Scopus ID:", doc_scopus_id )
				if 'prism:doi' in doc:
					doc_doi = doc['prism:doi']
					print( "    DOI (Document Object Identifier):", doc_doi )
				doc_eid = doc['eid']
				print( "    EID (Electronic ID):", doc_eid )
				print( "    Date:", doc['prism:coverDate'])
				print( "    Type:", doc['subtypeDescription'])

				## Scopus (Abtract) document example
				# Initialize document with ID as integer
				scp_doc = AbsDoc(scp_id = doc_scopus_id)
				if scp_doc.read(client):
					print()
					#pprint(vars(scp_doc))

					#print("scp_doc.title: ", scp_doc.title)
					
					print( "    Areas:", len(scp_doc._data['subject-areas']['subject-area']), end=' ' )
					keywords = []
					for keyword in scp_doc._data['subject-areas']['subject-area']:
						keywords.append(keyword['$'])
					print(keywords)

					try:
						print( "    Keywords:", len(scp_doc._data['idxterms']['mainterm']), end=' ' )
						keywords = []
						for keyword in scp_doc._data['idxterms']['mainterm']:
							keywords.append(keyword['$'])
						print(keywords)
					except:
						pass

					#print( scp_doc._data['item']['bibrecord']['head']['abstracts'] )
					scp_doc.write()   
				else:
					print ("    Read document failed.")

				if 'prism:doi' in doc:
					## ScienceDirect (full-text) document example using DOI
					doi_doc = FullDoc(doi = doc_doi)
					print()
					if doi_doc.read(client):
						print("    Full Text Available")
						#print ("doi_doc.title: ", doi_doc.title)
						#print ( doi_doc )
						doi_doc.write()   
					else:
						print ("    Read document failed.")









		else:
			print ("Read author failed.")

	################################################################################

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





print()


