import os
dir_path = os.path.dirname(os.path.realpath(__file__))
os.environ['PYB_CONFIG_FILE'] = os.path.join(dir_path, "config.ini")
from pybliometrics.scopus import AbstractRetrieval, AuthorRetrieval, AffiliationRetrieval

def scopus_h_index(author_id):
    try:
        au = AuthorRetrieval(author_id)
        return au.h_index
    except:
        return None

# TESTING

if False:

    f = open('colegas.csv', 'r', encoding='utf8')

    fout = open('info.csv', 'w', encoding='utf8')
    print('Nome', 'h-index', 'citations', 'documents', 'orcid', 'years', 'link', sep=';', file=fout)


    for a in f:
        items = a.strip().split(';')

        try:
            au = AuthorRetrieval(items[3])
            print(items[0], au.h_index, au.citation_count, au.document_count, au.orcid, au.publication_range, au.scopus_author_link)
            link = 'https://www.scopus.com/authid/detail.uri?authorId=' + items[3]
            print(items[0], au.h_index, au.citation_count, au.document_count, au.orcid, au.publication_range, link , sep=';', file=fout)
        except:
            print("Failed")

    fout.close()
