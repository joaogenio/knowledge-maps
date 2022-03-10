from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch
import json

from pprint import pprint

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

		area_freq					# {Area(name='Artificial Intelligence'): 10}
									# // Areas and the amount of times they
									# // appeared in the author's documents

		# TO DO'S

		# PEER REVIEWS
		# COURSES TAUGHT
		# ACTUATION DOMAINS
		#
		# PROJECTS
		# 
		# LANGUAGES
		
		
		
		):
		pass

class Affiliation:					# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Universidade de Aveiro
		scopus_id):					# 60024825
		pass

class Area:							# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Software
		abbreviation,				# COMP // Can be the same for many areas
		code):						# 1712
		pass

class Document:						# EXAMPLES // DESCRIPTION
	def __init__(self,
		name,						# Creating a Project track in a 5-year
									# integrated Engineering Curricullum
		scopus_id,					# 85124808238
		doi,						# 10.1109/WEEF/GEDC53299.2021.9657160
		eid,						# 2-s2.0-85124808238
		date,						# 2021-01-01
		type,						# Conference Paper
		area_list,					# [Area(), ...]
		keyword_list,				# ['Active Learning', 'Soft skills', ...]
		full_text					# // Full document text
		):
		pass

################################################################################

## Load configuration
con_file = open("config.json")
config = json.load(con_file)
con_file.close()

## Initialize client
client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']




## Initialize author search object and execute search
#auth_srch = ElsSearch('authlast(Neves) and authfirst(António J.R.)','author')
#auth_srch.execute(client)
#print ("auth_srch has", len(auth_srch.results), "results.")
#print ("results", auth_srch.results)



ids = ['43461712600', '57188881218', '57203431176', '57199578161', '49361962700', '54987996200']

for author_id in ids:

	## Author example
	# Initialize author with uri
	my_auth = ElsAuthor(
			uri = 'https://api.elsevier.com/content/author/author_id/' + author_id)
	# Read author data, then write to disk
	if my_auth.read(client):

		#pprint(vars(my_auth))



		### AUTHOR ###

		print("\n-----------------------------------------------")
		print(bcolors.OKGREEN + "\nAuthor:" , 		my_auth.full_name, bcolors.ENDC)
		author_scopus_id = 		my_auth._data['coredata']['dc:identifier'].split(':')[1]
		print("    Scopus ID:", author_scopus_id  )
		print("    ORCID ID:",  my_auth._data['coredata']['orcid']  )
		if 'name-variant' in my_auth._data['author-profile']:
			print("    Name Variants:",	len(my_auth._data['author-profile']['name-variant'])  )



		### AFFILIATION ###

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


