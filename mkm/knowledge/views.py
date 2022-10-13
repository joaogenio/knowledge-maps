from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .api_utils.tt_simple_api import *
from .api_utils.h_index import *
from knowledge.forms import *
from pprint import pprint
from datetime import datetime, date
import time
from django.db.models import Avg, Count, Min, Sum
from django.db.models import Q

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from difflib import SequenceMatcher

from rest_framework import serializers
from django.http import Http404

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

class PublicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationType
        fields = "__all__"

class AuthorSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"

class PublicationSerializer(serializers.ModelSerializer):
    publication_type = PublicationTypeSerializer()
    areas = AreaSerializer(many=True)
    author_set = AuthorSmallSerializer(many=True)

    class Meta:
        model = Publication
        fields = "__all__"

class AuthorSerializer(serializers.ModelSerializer):
    publications = PublicationSerializer(many=True)

    class Meta:
        model = Author
        fields = "__all__"

class AuthorSmallSerializer(serializers.ModelSerializer):
    short_name = serializers.ReadOnlyField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'short_name']

# Create your views here.

# Define important Publication Types for sorting
publication_types_options = ['Conference Paper', 'Book', 'Article']#, 'Review']
publication_types_options = sorted(publication_types_options)
publication_types_options.insert(0, 'All')
publication_types_options.append('Other')

def login_view(request):

    if not request.user.is_authenticated:

        # If authentication fails, report error
        auth_fail = False

        if request.method == 'POST':

            if 'username' in request.POST:

                username = request.POST['username']
                password = request.POST['password']
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return redirect('index')
                    
                else:
                    auth_fail = True
        
        context = {'auth_fail': auth_fail}
        return render(request, 'login.html', context)

    else: # User is authenticated

        if request.method == 'POST':

            if 'logout' in request.POST:
                
                logout(request)
                return redirect('login')

        return redirect('index')

def test1(request):

    graph = author_map(
        pk=7,
        #keywords=None,
        #doctype='All',
        #start_year=1980,
        #end_year=2022
    )

    context = {
        'nodes': graph['nodes'],
        'edges': graph['edges'],
    }

    return render(request, 'test1.html', context)

def test2(request):

    keywords = []
    query = ''
    a = text_pipeline(query)
    for keyword in Keyword.objects.all():
        b = text_pipeline(keyword.name)
        keyword_match = SequenceMatcher(None, a, b).ratio()
        if (keyword_match > 0.7 or contained(a, b)) and (a != '' and b != ''):
            keywords.append([keyword.name, True])
    
    #print(keywords)

    graph = global_map(
        keywords=keywords,
        doctype='All',
        start_year=1980,
        end_year=2022
    )

    context = {
        'nodes': graph['nodes'],
        'edges': graph['edges'],
    }

    return render(request, 'test2.html', context)

def test3(request):

    publications = Publication.objects.all()

    counters = {}

    for publication in publications:

        publication_type_name = publication.publication_type.name

        if not publication_type_name in counters:
            counters[publication_type_name] = 1
        else:
            counters[publication_type_name] += 1
    
    pprint(counters)

    context = {}
    return render(request, 'test3.html', context)

def author_map(pk, keywords=None, doctype='All', start_year=date(1980, 1, 1).year, end_year=date.today().year):

    # keywords = [ ['robotics', True], ['health', False], ... ]
    # Use only 'True' ones, aka 'keywords[index][1]'

    authors = Author.objects.prefetch_related(
        'projects__areas',
        'publications__author_set',
        'publications__keywords',
        'publications__areas',
        'publications__publication_type',
        'domains',
        'current_affiliations',
        'previous_affiliations'
    ).all()

    # Graph data
    nodes = [] # contains authors ids, names, and total number of publications
    edges = [] # tells which authors are connected by how many publications

    # Contains the actual publications from the 'edges' list
    edges_publications = {}

    ###########################
    # Add author              #
    ###########################
    author = authors.get(pk=pk)
    nodes.append(author)
    # Contains the actual publications from the 'nodes' list
    nodes_authors = {
        f'{author.pk}': dict(AuthorSmallSerializer(author).data)
    }

    ##################################################
    # Add author publications                        #
    ##################################################
    nodes_authors[f'{author.pk}']['publications'] = []
    for publication in author.publications.all():

        # Check if date is out of range
        if publication.date.year < start_year or publication.date.year > end_year:
            continue

        if doctype == 'Other':
            if publication.publication_type.name in publication_types_options:
                continue
        elif doctype != 'All': # types from the selection
            if publication.publication_type.name != doctype:
                continue
        
        if keywords == None:
            nodes_authors[f'{author.pk}']['publications'].append(dict(PublicationSerializer(publication).data))
        else:
            for keyword in keywords:

                if keyword[1]:

                    keyword = Keyword.objects.get(name=keyword[0])

                    if len(publication.keywords.all()) != 0 and keyword in publication.keywords.all():

                        nodes_authors[f'{author.pk}']['publications'].append(dict(PublicationSerializer(publication).data))
                        break

    ###########################################################################
    # Iterate every author                                                    #
    # We want to find which authors have publications in common with this one #
    ###########################################################################
    for colleague in authors:
        count = 0 # number of publications together

        if author.pk != colleague.pk: # author.pk < colleague.pk:

            #############################################
            # Iterate this author's publications        #
            #############################################
            for publication in author.publications.all():

                # Check if date is out of range
                if publication.date.year < start_year or publication.date.year > end_year:
                    continue

                if doctype == 'Other':
                    if publication.publication_type.name in publication_types_options:
                        continue
                elif doctype != 'All': # types from the selection
                    if publication.publication_type.name != doctype:
                        continue
                
                ####################
                # No keywords      #
                ####################
                if keywords == None:

                    if colleague in publication.author_set.all():

                        count += 1 # increase number of publications that both authors have in common
                        
                        key = f"{min(author.pk, colleague.pk)}-{max(author.pk, colleague.pk)}"
                        if not key in edges_publications:
                            edges_publications[key] = {'publications': [ dict(PublicationSerializer(publication).data) ] }

                            #pprint(dict(PublicationSerializer(publication).data))
                        else:
                            edges_publications[key]['publications'].append( dict(PublicationSerializer(publication).data) )
                        
                        edges_publications[key]['author_1'] = dict(AuthorSmallSerializer(author).data)
                        edges_publications[key]['author_2'] = dict(AuthorSmallSerializer(colleague).data)

                #################
                # With keywords #
                #################
                else:

                    if colleague in publication.author_set.all():

                        ########################
                        # Iterate keywords     #
                        ########################
                        for keyword in keywords:

                            if keyword[1]:

                                keyword = Keyword.objects.get(name=keyword[0])

                                if len(publication.keywords.all()) != 0 and keyword in publication.keywords.all():

                                    count += 1 # increase number of publications that both authors have in common
                                    
                                    key = f"{min(author.pk, colleague.pk)}-{max(author.pk, colleague.pk)}"
                                    if not key in edges_publications:
                                        edges_publications[key] = {'publications': [ dict(PublicationSerializer(publication).data) ] }
                                        #pprint(dict(PublicationSerializer(publication).data))
                                    else:
                                        edges_publications[key]['publications'].append( dict(PublicationSerializer(publication).data) )
                                    
                                    edges_publications[key]['author_1'] = dict(AuthorSmallSerializer(author).data)
                                    edges_publications[key]['author_2'] = dict(AuthorSmallSerializer(colleague).data)

                                    # This publication contains at least one keyword from our selection
                                    # No need to check the other keywords in our selection
                                    break

        #################################################################
        # Colleague has at least one publication in common              #
        # It's a collaborator. Add it and its publications to the graph #
        #################################################################
        if count != 0:
            edges.append([author.pk, colleague.pk, count])

            if colleague not in nodes:

                nodes.append(colleague)

                nodes_authors[f'{colleague.pk}'] = dict(AuthorSmallSerializer(colleague).data)
                nodes_authors[f'{colleague.pk}']['publications'] = []

                for publication in colleague.publications.all():

                    # Check if date is out of range
                    if publication.date.year < start_year or publication.date.year > end_year:
                        continue

                    if doctype == 'Other':
                        if publication.publication_type.name in publication_types_options:
                            continue
                    elif doctype != 'All': # types from the selection
                        if publication.publication_type.name != doctype:
                            continue

                    if keywords == None:
                        nodes_authors[f'{colleague.pk}']['publications'].append(dict(PublicationSerializer(publication).data))
                    else:
                        for keyword in keywords:

                            if keyword[1]:

                                keyword = Keyword.objects.get(name=keyword[0])

                                if len(publication.keywords.all()) != 0 and keyword in publication.keywords.all():

                                    nodes_authors[f'{colleague.pk}']['publications'].append(dict(PublicationSerializer(publication).data))
                                    
                                    # This publication contains at least one keyword from our selection
                                    # No need to check the other keywords in our selection
                                    break
    
    #############################################################################
    # Same process but only between the author's colleagues                     #
    # This prevents the graph from expanding to a global level                  #
    # Data is confined to the connections between the author and his colleagues #
    # and between the colleagues in that same set.                              #
    #############################################################################
    for colleague in nodes:

        for other in nodes:
            count = 0 # number of publications together

            if colleague.pk < other.pk and colleague.pk != author.pk and other.pk != author.pk:

                #############################################
                # Iterate this colleague's publications     #
                #############################################
                for publication in colleague.publications.all():

                    # Check if date is out of range
                    if publication.date.year < start_year or publication.date.year > end_year:
                        continue

                    if doctype == 'Other':
                        if publication.publication_type.name in publication_types_options:
                            continue
                    elif doctype != 'All': # types from the selection
                        if publication.publication_type.name != doctype:
                            continue

                    ####################
                    # No keywords      #
                    ####################
                    if keywords == None:

                        if other in publication.author_set.all():
                            count += 1 # increase number of publications that both authors have in common

                            key = f"{min(colleague.pk, other.pk)}-{max(colleague.pk, other.pk)}"
                            if not key in edges_publications:
                                edges_publications[key] = {'publications': [ dict(PublicationSerializer(publication).data) ] }
                            else:
                                edges_publications[key]['publications'].append( dict(PublicationSerializer(publication).data) )
                            
                            edges_publications[key]['author_1'] = dict(AuthorSmallSerializer(colleague).data)
                            edges_publications[key]['author_2'] = dict(AuthorSmallSerializer(other).data)

                    #################
                    # With keywords #
                    #################
                    else:

                        if other in publication.author_set.all():

                            ########################
                            # Iterate keywords     #
                            ########################
                            for keyword in keywords:

                                if keyword[1]:

                                    keyword = Keyword.objects.get(name=keyword[0])

                                    if len(publication.keywords.all()) != 0 and keyword in publication.keywords.all():

                                        count += 1 # increase number of publications that both authors have in common

                                        key = f"{min(colleague.pk, other.pk)}-{max(colleague.pk, other.pk)}"
                                        if not key in edges_publications:
                                            edges_publications[key] = {'publications': [ dict(PublicationSerializer(publication).data) ] }
                                        else:
                                            edges_publications[key]['publications'].append( dict(PublicationSerializer(publication).data) )
                                        
                                        edges_publications[key]['author_1'] = dict(AuthorSmallSerializer(colleague).data)
                                        edges_publications[key]['author_2'] = dict(AuthorSmallSerializer(other).data)
                                        
                                        break

            ##############################################################################################
            # These colleagues have at least one publication in common                                   #
            # They're collaborators. Add it and its publications to the graph                            #
            # Difference is that they have already been added to the graph along with their publications #
            ##############################################################################################
            if count != 0:
                edges.append([colleague.pk, other.pk, count])
    
    #for key in nodes_authors:
        #print(nodes_authors[key]['name'])
        #pprint(nodes_authors[key])
    
    #for key in edges_publications:
    #    print(key + ' (' + str(len(edges_publications[key])) + ')')
        #for publication in edges_publications[key]:
        #    print(publication['title'])
    
    return {'nodes': nodes, 'edges': edges, 'nodes_authors': nodes_authors, 'edges_publications': edges_publications}

def global_map(keywords=[], doctype='All', start_year=date(1980, 1, 1).year, end_year=date.today().year):

    # Graph data
    nodes = [] # contains authors ids, names, and total number of publications
    edges = [] # tells which authors are connected by how many publications

    # Contains the actual publications from the 'edges' list
    edges_publications = {}
    # Contains the actual publications from the 'nodes' list
    nodes_authors = {}

    ###############################
    # Fetch relevant publications #
    ###############################
    true_keywords = []
    for keyword in keywords:
        if keyword[1]:
            true_keywords.append(keyword[0])

    #print(true_keywords)

    if doctype == 'Other': # exclude types from the selection (Examples: "Book Chapter", "Report")

        valid_types = PublicationType.objects.exclude(
            name__in = publication_types_options
        ).values('name')
        #print(valid_types)

        if true_keywords == []:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                ),
                publication_type__name__in = valid_types
            ).distinct()
        else:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                ),
                publication_type__name__in = valid_types,
                keywords__name__in = true_keywords
            ).distinct()

        #for x in publications:
        #    print(x.pretty())

        #print(publications.count())

    elif doctype != 'All': # types from the selection (Examples: "Conference Paper", "Article", "Book")

        publication_type = PublicationType.objects.get(name=doctype)

        if true_keywords == []:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                ),
                publication_type = publication_type
            ).distinct()
        else:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                ),
                publication_type = publication_type,
                keywords__name__in = true_keywords
            ).distinct()

        #print(publications.count())

    else: # All types

        if true_keywords == []:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                )
            ).distinct()
        else:
            publications = Publication.objects.filter(
                date__range = (
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                ),
                keywords__name__in = true_keywords
            ).distinct()

        #print(publications.count())
    
    ################################
    # Iterate all publications     #
    ################################
    for publication in publications:

        author_set = publication.author_set.all()

        for author in author_set:

            # Add author
            if not author in nodes:
                nodes.append(author)
            if not f'{author.pk}' in nodes_authors:
                nodes_authors[f'{author.pk}'] = dict(AuthorSmallSerializer(author).data)
                nodes_authors[f'{author.pk}']['publications'] = []

            # Add to author's publications
            nodes_authors[f'{author.pk}']['publications'].append(dict(PublicationSerializer(publication).data))

            # Iterate pairs
            for colleague in author_set:

                # Easy way to iterate every pair of authors, without
                # repeating the same pair in the reverse order and,
                # of course, without testing the an author against himself
                if colleague.pk >= author.pk:
                    continue
                
                # Add publication to edges
                key = f"{min(author.pk, colleague.pk)}-{max(author.pk, colleague.pk)}"

                if not key in edges_publications:
                    edges_publications[key] = {'publications': [ dict(PublicationSerializer(publication).data) ] }
                else:
                    edges_publications[key]['publications'].append( dict(PublicationSerializer(publication).data) )
                
                edges_publications[key]['author_1'] = dict(AuthorSmallSerializer(author).data)
                edges_publications[key]['author_2'] = dict(AuthorSmallSerializer(colleague).data)

    # Build edges
    for key in edges_publications:
        s = key.split('-')
        author_1 = s[0]
        author_2 = s[1]
        edges.append([ int(author_1), int(author_2), len(edges_publications[key]['publications']) ])

    return {'nodes': nodes, 'edges': edges, 'nodes_authors': nodes_authors, 'edges_publications': edges_publications}

def test4(request):
    return render(request, 'test4.html', context)

def test5(request):
    return render(request, 'test5.html', context)

#############################################################
###   revert doi saving. we need to keep the underscore   ###
#############################################################

def index_view(request):

    if request.user.is_authenticated:
        
        if request.method == 'POST':

            if 'delpubs' in request.POST:

                publications = Publication.objects.all()
                for publication in publications:
                    publication.delete()
            
            # Populate DB (SC -> CV)
            if 'test1' in request.POST:

                authors = Author.objects.all()

                counters_sc = {
                    'new': 0,
                    's_sc': 0,
                        's_sc_d_cv': 0,
                        's_sc_d_doi': 0,
                    's_cv': 0,
                        's_cv_d_sc': 0,
                        's_cv_d_doi': 0,
                    's_doi': 0,
                        's_doi_d_sc': 0,
                        's_doi_d_cv': 0,
                    's_abstract': 0,
                    's_title': 0,
                    's_title_contained': 0,
                }

                counters_cv = counters_sc.copy()

                for author in authors:

                    print(f"{author.pk} - {author.name}")

                    #if author.pk == 15 or author.pk == 7:

                    y = sync_scopus_docs(author.pk)
                    counters_sc = {k: counters_sc.get(k, 0) + y.get(k, 0) for k in set(counters_sc) & set(y)}

                    y = sync_ciencia(author.pk)
                    counters_cv = {k: counters_cv.get(k, 0) + y.get(k, 0) for k in set(counters_cv) & set(y)}

                print('')
                print(f"new                {counters_sc['new']}")
                print('')
                print(f"s_sc               {counters_sc['s_sc']}")
                print(f"|_ s_sc_d_cv       |_ {counters_sc['s_sc_d_cv']}")
                print(f"|_ s_sc_d_doi      |_ {counters_sc['s_sc_d_doi']}")
                print('')
                print(f"s_cv               {counters_sc['s_cv']}")
                print(f"|_ s_cv_d_sc       |_ {counters_sc['s_cv_d_sc']}")
                print(f"|_ s_cv_d_doi      |_ {counters_sc['s_cv_d_doi']}")
                print('')
                print(f"s_doi              {counters_sc['s_doi']}")
                print(f"|_ s_doi_d_sc      |_ {counters_sc['s_doi_d_sc']}")
                print(f"|_ s_doi_d_cv      |_ {counters_sc['s_doi_d_cv']}")
                print('')
                print(f"s_abstract         {counters_sc['s_abstract']}")
                print(f"s_title            {counters_sc['s_title']}")
                print(f"s_title_contained  {counters_sc['s_title_contained']}")
                print('')
                print(f"new                {counters_cv['new']}")
                print('')
                print(f"s_sc               {counters_cv['s_sc']}")
                print(f"|_ s_sc_d_cv       |_ {counters_cv['s_sc_d_cv']}")
                print(f"|_ s_sc_d_doi      |_ {counters_cv['s_sc_d_doi']}")
                print('')
                print(f"s_cv               {counters_cv['s_cv']}")
                print(f"|_ s_cv_d_sc       |_ {counters_cv['s_cv_d_sc']}")
                print(f"|_ s_cv_d_doi      |_ {counters_cv['s_cv_d_doi']}")
                print('')
                print(f"s_doi              {counters_cv['s_doi']}")
                print(f"|_ s_doi_d_sc      |_ {counters_cv['s_doi_d_sc']}")
                print(f"|_ s_doi_d_cv      |_ {counters_cv['s_doi_d_cv']}")
                print('')
                print(f"s_abstract         {counters_cv['s_abstract']}")
                print(f"s_title            {counters_cv['s_title']}")
                print(f"s_title_contained  {counters_cv['s_title_contained']}")

                publications = Publication.objects.all()
                author_count = {}

                for publication in publications:

                    count = publication.author_set.all().count()
                    if not count in author_count:
                        author_count[count] = 1
                    else:
                        author_count[count] += 1
                
                for key in author_count:
                    print(key, author_count[key])
            
            # Something
            if 'test2' in request.POST:

                publications = Publication.objects.all()

                names = {
                    'manual': 0,
                    'Manual': 0,
                    'MANUAL': 0
                }

                for publication in publications:
                    if publication.publication_type.name in names.keys():
                        names[publication.publication_type.name] += 1
                
                print(names)
            
            # Order Analysis
            if 'test3' in request.POST:

                authors = Author.objects.all()
                firstdone = False

                for author in authors:
                    pk = author.pk

                    if firstdone:
                        break
                    ### uncomment to debug a specific author
                    firstdone = True
                    pk = 62
                    author = Author.objects.get(pk=pk)

                    pubs_a = []
                    pubs_b = []

                    print("\n")
                    print(author.pk, author.name)

                    if True:

                        # pubs 'B' CV -> SC

                        publications = Publication.objects.all()
                        for publication in publications:
                            publication.delete()

                        sync_ciencia(pk)
                        sync_scopus_docs(pk)
                        with open(f'{author.scopus_id}_pubs_b.txt', 'w', encoding="utf-8") as f:
                            pubs = author.publications.order_by('scopus_id', 'date', 'title', 'publication_type')
                            for pub in pubs:
                                sc_id = pub.scopus_id
                                pubs_b.append(pub.pretty().replace('\n', ''))
                                f.write("{}\n".format(pub.pretty().replace('\n', '')))
                        
                        # pubs 'A' SC -> CV
                        
                        publications = Publication.objects.all()
                        for publication in publications:
                            publication.delete()

                        sync_scopus_docs(pk)
                        sync_ciencia(pk)
                        with open(f'{author.scopus_id}_pubs_a.txt', 'w', encoding="utf-8") as f:
                            pubs = author.publications.order_by('scopus_id', 'date', 'title', 'publication_type')
                            for pub in pubs:
                                sc_id = pub.scopus_id
                                #print("\n" + str(sc_id), end=" ")
                                #if sc_id in ids and sc_id != None:
                                #    print("wtf", end="        ")
                                #else:
                                #    print("", end="           ")
                                #print(pub.pretty())
                                pubs_a.append(pub.pretty().replace('\n', ''))
                                f.write("{}\n".format(pub.pretty().replace('\n', '')))
                    
                    #pubs_a = [   1,    3, None,    6,    8]
                    #pubs_b = [0,    2, 3, 4,    5, 6, 7]
                    pubs_a = []
                    pubs_b = []

                    with open(f'{author.scopus_id}_pubs_a.txt', 'r', encoding="utf-8") as f:
                        for line in f:
                            pubs_a.append(line)
                    with open(f'{author.scopus_id}_pubs_b.txt', 'r', encoding="utf-8") as f:
                        for line in f:
                            pubs_b.append(line)

                    end_a = False
                    end_b = False
                    idx_a = 0
                    idx_b = 0
                    while not end_a and not end_b:
                        if idx_a == len(pubs_a):
                            end_a = True
                            a = None
                            aid = None
                        else:
                            a = pubs_a[idx_a]
                            if pubs_a[idx_a].split(' ')[0] != None:
                                #aid = int(pubs_a[idx_a].scopus_id)
                                aid = pubs_a[idx_a].split(' ')[0]
                            else:
                                aid = None
                        if idx_b == len(pubs_b):
                            end_b = True
                            b = None
                            bid = None
                        else:
                            b = pubs_b[idx_b]
                            if pubs_b[idx_b].split(' ')[0] != None:
                                #bid = int(pubs_b[idx_b].scopus_id)
                                bid = pubs_b[idx_b].split(' ')[0]
                            else:
                                bid = None

                        sep = "-"*(103+3+103) + '\n'

                        sa1 = sep + "{}]  ".format( '] '.join(a.split('] ')[:-1]) ) if aid != None else None
                        sa2 = "{:<103}  ".format( a.split('] ')[-1][:-1][:103] ) if aid != None else None

                        sb1 = "{}]  ".format( '] '.join(b.split('] ')[:-1]) ) if bid != None else None
                        sb2 = "{:<103}  ".format( b.split('] ')[-1][:-1][:103] ) if bid != None else None

                        pad = " "*(103+2)
                        
                        if(a in pubs_b):
                            if aid == bid:
                                #print(sa1, sb1)
                                #print(sa2, sb2)
                                idx_a += 1
                                idx_b += 1
                            elif aid < bid:
                                print(sa1)
                                print(sa2)
                                idx_a += 1
                            else:
                                print(sep + pad, sb1)
                                print(pad, sb2)
                                idx_b += 1
                        else:
                            if aid != None:
                                if bid != None:
                                    if aid < bid:
                                        print(sa1)
                                        print(sa2)
                                        idx_a += 1
                                    else:
                                        print(sep + pad, sb1)
                                        print(pad, sb2)
                                        idx_b += 1
                                else:
                                    print(sa1)
                                    print(sa2)
                                    idx_a += 1
                            else:
                                if bid != None:
                                    print(sep + pad, sb1)
                                    print(pad, sb2)
                                    idx_b += 1

                        if aid == None:
                            idx_a += 1
                        if bid == None:
                            idx_b += 1
                    
                    print(sep)
                    print(len(pubs_a), len(pubs_b))
       
            # Text Analysis
            if 'test' in request.POST:

                authors = Author.objects.prefetch_related(
                    'projects__areas',
                    'publications__author_set',
                    'publications__keywords',
                    'publications__areas',
                    'publications__publication_type',
                    'domains',
                    'current_affiliations',
                    'previous_affiliations'
                ).annotate(num_publications=Count('publications')).order_by('-num_publications')#[:20]

                erratum_id = PublicationType.objects.get(name='Erratum')

                matches = 0
                total = 0
                i = 1

                same_scopus = 0
                same_ciencia = 0
                same_doi = 0

                # Id's of iterated publications
                # We want to test A vs B. But then B vs A will be unnecessary
                iterated_pubs = []

                firstdone = False

                for author in authors:

                    pk = author.pk

                    if firstdone:
                        break
                    ### uncomment to debug a specific author
                    firstdone = True
                    pk = 62#7#15#39#38#47#55
                    author = Author.objects.get(pk=pk)

                    print("\n")
                    print(author.pk, author.name)

                    publications = author.publications.all()
                    
                    for publication in publications:

                        if publication.publication_type != erratum_id:

                            iterated_pubs.append(publication.pk)

                            # NAME TEST
                            a = text_pipeline(publication.title)

                            for test in publications:
                                if test.pk not in iterated_pubs and \
                                    publication.pk != test.pk and \
                                    test.publication_type != erratum_id and \
                                    test.publication_type == publication.publication_type and \
                                    publication.date.year == test.date.year:
                                    
                                    # NAME TEST
                                    b = text_pipeline(test.title)

                                    # https://www.educative.io/answers/what-is-sequencematcher-in-python
                                    match = SequenceMatcher(None, a, b).ratio()

                                    abstract_count = 0
                                    if publication.abstract != "":
                                        abstract_count += 1
                                    if test.abstract != "":
                                        abstract_count += 1
                                    
                                    f_same_scopus = False
                                    f_same_ciencia = False
                                    f_same_doi = False
                                    if publication.scopus_id == test.scopus_id and publication.scopus_id != None:
                                        same_scopus += 1
                                        f_same_scopus = True
                                    if publication.ciencia_id == test.ciencia_id and publication.ciencia_id != None:
                                        same_ciencia += 1
                                        f_same_ciencia = True
                                    if publication.doi == test.doi and publication.doi != None:
                                        same_doi += 1
                                        f_same_doi = True

                                    if match > 0.7:# and abstract_count == 0:# and match != 1:

                                        sa = publication.pretty()
                                        sb = test.pretty()

                                        sep = "-"*(103+3+103) + '\n'

                                        sa1 = sep + "{}]  ".format( '] '.join(sa.split('] ')[:-1]) )
                                        sa2 = "{:<103}  ".format( sa.split('] ')[-1].replace('\n', '')[:103] )
                                        sa3 = "{:<103}  ".format( a[:103] )
                                        sa4 = "{:<103}  ".format( publication.abstract[:103] )

                                        sb1 = "{}]  ".format( '] '.join(sb.split('] ')[:-1]) )
                                        sb2 = "{:<103}  ".format( sb.split('] ')[-1].replace('\n', '')[:103] )
                                        sb3 = "{:<103}  ".format( b[:103] )
                                        sb4 = "{:<103}  ".format( test.abstract[:103] )

                                        if False: # Use false for screenshots

                                            print(sa1, sb1)
                                            print(sa2, sb2)

                                            if match == 1:
                                                color = bcolors.OKGREEN
                                            elif contained(a, b, dbg=False):#a in b or b in a:
                                                color = bcolors.OKBLUE
                                            else:
                                                color = bcolors.WARNING
                                            print(f"{color}{sa3} {sb3}{bcolors.ENDC}")
                                            print("{}{}Title: {:.3f}{}".format(98*' ', color, match, bcolors.ENDC))
                                            
                                            match = 'N/A'
                                            color = bcolors.WARNING
                                            if publication.abstract != '' and test.abstract != '':
                                                abstract_a = text_pipeline(publication.abstract)
                                                abstract_b = text_pipeline(test.abstract)
                                                match = SequenceMatcher(None, abstract_a, abstract_b).ratio()
                                                color = bcolors.OKGREEN if match > 0.95 else bcolors.FAIL
                                                match = '{:.3f}'.format( match )
                                            print(f"{color}{sa4} {sb4}{bcolors.ENDC}")
                                            print("{}{}Abstract: {}{}".format(95*' ', color, match, bcolors.ENDC))
                                        
                                        else:

                                            print(sa1)
                                            print(sa2)
                                            print("vs")
                                            print(sb1)
                                            print(sb2)
                                            print()

                                            if match == 1:
                                                color = bcolors.OKGREEN
                                            elif contained(a, b, dbg=False):#a in b or b in a:
                                                color = bcolors.OKBLUE
                                            else:
                                                color = bcolors.WARNING

                                            print(f"{color}{sa3}{bcolors.ENDC}")
                                            print("vs")
                                            print(f"{color}{sb3}{bcolors.ENDC}")
                                            print("Title: {:.3f}{}".format(match, bcolors.ENDC))
                                            print()

                                            match = 'N/A'
                                            color = bcolors.WARNING
                                            if publication.abstract != '' and test.abstract != '':
                                                abstract_a = text_pipeline(publication.abstract)
                                                abstract_b = text_pipeline(test.abstract)
                                                match = SequenceMatcher(None, abstract_a, abstract_b).ratio()
                                                color = bcolors.OKGREEN if match > 0.95 else bcolors.FAIL
                                                match = '{:.3f}'.format( match )

                                            sa4 = 'N/A' if publication.abstract == '' else sa4
                                            sb4 = 'N/A' if test.abstract == '' else sb4

                                            print(f"{color}{sa4}{bcolors.ENDC}")
                                            print("vs")
                                            print(f"{color}{sb4}{bcolors.ENDC}")
                                            print("Abstract: {}{}".format(match, bcolors.ENDC))


                                        #print()
                                        #print(a)
                                        #print(b)
                                        ##print(match, publication.pk, test.pk)
                                        #print()
                                        #print(publication.publication_type.name + "s")
                                        #print(publication.pk, "[{}]".format( str(publication.date) ), "("+str(len(publication.author_set.all()))+")", publication.title)
                                        #print(publication.scopus_id, publication.ciencia_id, publication.doi, publication.from_scopus, publication.from_ciencia)
                                        #print("vs")
                                        #print(test.pk, "[{}]".format( str(test.date) ), "("+str(len(test.author_set.all()))+")", test.title)
                                        #print(test.scopus_id, test.ciencia_id, test.doi, test.from_scopus, test.from_ciencia)
                                        #print("\nMatch:", match)
                                        #print("\n" + publication.abstract[:300])
                                        #print("vs")
                                        #print(test.abstract[:300])

                                        #print("\nSame? [y/n] ")
                                        #x = None
                                        #while(x != 'y' and x != 'n'):
                                        #    x = input()
                                        #if x == 'y':
                                        #    matches += 1
                                        matches += 1
                                    
                                    total += 1
                            
                print("\nmatches: " + str(matches) + " out of " + str(total))
                print("same_scopus: " + str(same_scopus) + " out of " + str(total))
                print("same_ciencia: " + str(same_ciencia) + " out of " + str(total))
                print("same_doi: " + str(same_doi) + " out of " + str(total))
                print()



            if 'add-author' in request.POST:
                authorform = AuthorForm(request.POST)
                if authorform.is_valid():
                    clean = authorform.cleaned_data
                    author = Author(
                        scopus_id = clean['scopus_id'],
                        ciencia_id = clean['ciencia_id'],
                        orcid_id = clean['orcid_id']
                    )
                    author.save()
            
            if 'delete_author' in request.POST:
                pk = request.POST['author_pk']
                author = Author.objects.get(pk=pk)
                author.delete()


            # Sync operations
            elif 'sync-scopus-docs' in request.POST:
                pk = request.POST['author_pk']
                sync_scopus_docs(pk)

            elif 'sync-scopus-author' in request.POST:
                pk = request.POST['author_pk']
                sync_scopus_author(pk)
                
            elif 'sync-ciencia' in request.POST:
                pk = request.POST['author_pk']
                sync_ciencia(pk)
            

            # Publications Chart
            elif 'publication-type' in request.POST:
                request.session['index-publication-type'] = request.POST['publication-type']
            elif 'publication-start' in request.POST:
                request.session['index-publication-start'] = int(request.POST['publication-start'])
            elif 'publication-end' in request.POST:
                request.session['index-publication-end'] = int(request.POST['publication-end'])

            # Projects Chart
            elif 'project-start' in request.POST:
                request.session['index-project-start'] = int(request.POST['project-start'])
            elif 'project-end' in request.POST:
                request.session['index-project-end'] = int(request.POST['project-end'])
        
            # Map
            elif 'reset-keyword' in request.POST:
                request.session.pop('index-keyword-search', None)
                request.session.pop('index-keywords-list', None)
            elif 'keyword-search' in request.POST:
                query = request.POST['keyword-search']
                if query != '':
                    request.session['index-keyword-search'] = query
                    request.session['index-keywords-list'] = []

                    a = text_pipeline(query)
                    for keyword in Keyword.objects.all():
                        b = text_pipeline(keyword.name)
                        keyword_match = SequenceMatcher(None, a, b).ratio()
                        if (keyword_match > 0.7 or contained(a, b)) and (a != '' and b != ''):
                            #print()
                            #print(query, '____', keyword.name)
                            #print(contained(a, b), a, '____', keyword_match, '____', b,)
                            request.session['index-keywords-list'].append([keyword.name, True])
                else:
                    request.session.pop('index-keyword-search', None)
                    request.session.pop('index-keywords-list', None)
            elif 'keyword-update' in request.POST and 'index-keywords-list' in request.session:
                for keyword in request.session['index-keywords-list']:
                    keyword[1] = False
                for index in request.POST:
                    if index.isnumeric():
                        if int(index) >= 0 and int(index) < len(request.session['keywords-list']):
                            request.session['index-keywords-list'][int(index)][1] = True
            elif 'map_publication_type' in request.POST:
                request.session['index_map_publication_type'] = request.POST['map_publication_type']
            elif 'map_publication_start' in request.POST:
                request.session['index_map_publication_start'] = int(request.POST['map_publication_start'])
            elif 'map_publication_end' in request.POST:
                request.session['index_map_publication_end'] = int(request.POST['map_publication_end'])

        # Session initialization

        if not 'index-keyword-search' in request.session:
            request.session['index-keyword-search'] = ''
        if not 'index-keywords-list' in request.session:
            request.session['index-keywords-list'] = []

        # Publication types and dates

        try:
            earliest_publication = Publication.objects.earliest('date')
            latest_publication = Publication.objects.latest('date')

            # Publications Chart
            if not 'index-publication-type' in request.session:
                request.session['index-publication-type'] = "Conference Paper"
            if not 'index-publication-start' in request.session:
                request.session['index-publication-start'] = earliest_publication.date.year
            if not 'index-publication-end' in request.session:
                request.session['index-publication-end'] = latest_publication.date.year
            
            publication_start_range = list(reversed(range(earliest_publication.date.year, request.session['index-publication-end'] + 1)))
            publication_end_range = list(reversed(range(request.session['index-publication-start'], latest_publication.date.year + 1)))

            # Map
            if not 'index_map_publication_type' in request.session:
                request.session['index_map_publication_type'] = "All"
            if not 'index_map_publication_start' in request.session:
                request.session['index_map_publication_start'] = earliest_publication.date.year
            if not 'index_map_publication_end' in request.session:
                request.session['index_map_publication_end'] = latest_publication.date.year
            
            map_start_range = list(reversed(range(earliest_publication.date.year, request.session['index_map_publication_end'] + 1)))
            map_end_range = list(reversed(range(request.session['index_map_publication_start'], latest_publication.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_publication = None
            latest_publication = None

            publication_start_range = None
            publication_end_range = None

            map_start_range = None
            map_end_range = None
        
        # Projects Chart dates
        try:
            earliest_project = Project.objects.earliest('date')
            latest_project = Project.objects.latest('date')

            if not 'index-project-start' in request.session:
                request.session['index-project-start'] = earliest_project.date.year
            if not 'index-project-end' in request.session:
                request.session['index-project-end'] = latest_project.date.year
            
            project_start_range = list(reversed(range(earliest_project.date.year, request.session['index-project-end'] + 1)))
            project_end_range = list(reversed(range(request.session['index-project-start'], latest_project.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_project = None
            latest_project = None
            project_start_range = None
            project_end_range = None


        # Charts
    
        labels_publications, data_publications = documents_from_year_interval(
            'Publication',
            request.session['index-publication-start'],
            request.session['index-publication-end'],
            pub_type=request.session['index-publication-type'],
            pub_types=publication_types_options.copy()
        )
        labels_projects, data_projects = documents_from_year_interval(
            'Project',
            request.session['index-project-start'],
            request.session['index-project-end'],
        )
        
        authorform = AuthorForm()
        
        authors = Author.objects.prefetch_related(  
            'projects__areas',
            'publications__author_set',
            'publications__keywords',
            'publications__areas',
            'publications__publication_type',
            'domains',
            'current_affiliations',
            'previous_affiliations'
        ).annotate(num_publications=Count('publications')).order_by('-num_publications')#[:20]

        cnt_publications = Publication.objects.all().count()
        cnt_projects = Project.objects.all().count()
        cnt_keywords = Keyword.objects.all().count()
        cnt_areas = Area.objects.all().count()

        # Build collaboration map
        if 'index-keywords-list' in request.session:
            search_keywords = request.session['index-keywords-list']
            valid_keywords = 0
            for keyword in search_keywords:
                if keyword[1]:
                    valid_keywords += 1
        else:
            search_keywords = None
            valid_keywords = 0

        graph = global_map(
            keywords = search_keywords,
            doctype = request.session['index_map_publication_type'],
            start_year = request.session['index_map_publication_start'],
            end_year = request.session['index_map_publication_end'],
        )

        search_keyword = request.session['index-keyword-search'] if 'index-keyword-search' in request.session else None

        # Context build

        context = {
            'user': request.user,

            'authorform': authorform,

            'authors': authors,

            # Publications Chart
            'publication_types': publication_types_options,
            'publication_type': request.session['index-publication-type'],
            'publication_start': request.session['index-publication-start'],
            'publication_end': request.session['index-publication-end'],
            'publication_start_range': publication_start_range,
            'publication_end_range': publication_end_range,

            # Projects Chart
            'project_start': request.session['index-project-start'],
            'project_end': request.session['index-project-end'],
            'project_start_range': project_start_range,
            'project_end_range': project_end_range,

            # Stats
            'cnt_publications': cnt_publications,
            'cnt_projects': cnt_projects,
            'cnt_keywords': cnt_keywords,
            'cnt_areas': cnt_areas,

            # Charts data
            'labels_publications': labels_publications,
            'data_publications': data_publications,
            'total_data_publications': sum(data_publications),

            'labels_projects': labels_projects,
            'data_projects': data_projects,
            'total_data_projects': sum(data_projects),

            # Collaboration map
            'nodes': graph['nodes'],
            'edges': graph['edges'],
            'nodes_authors': graph['nodes_authors'],
            'edges_publications': graph['edges_publications'],

            'search_keyword': search_keyword,
            'search_keywords': search_keywords,
            'valid_keywords': valid_keywords,
            'map_publication_type': request.session['index_map_publication_type'],

            'map_publication_start': request.session['index_map_publication_start'],
            'map_publication_end': request.session['index_map_publication_end'],
            'map_start_range': map_start_range,
            'map_end_range': map_end_range,
        }
        
        return render(request, 'index.html', context)

    return redirect('login')

def author_detail_view(request, pk):

    if request.user.is_authenticated:

        #del request.session['publication-type']
        #del request.session['publication-start']
        #del request.session['publication-end']
        
        #del request.session['keyword-search']
        #del request.session['keywords-list']

        try:
            this_author = Author.objects.get(pk = pk)
        except Author.DoesNotExist:
            raise Http404('Author does not exist')

        if request.method == 'POST':
            
            # Publications Chart
            if 'publication-type' in request.POST:
                request.session['publication-type'] = request.POST['publication-type']
            elif 'publication-start' in request.POST:
                request.session['publication-start'] = int(request.POST['publication-start'])
            elif 'publication-end' in request.POST:
                request.session['publication-end'] = int(request.POST['publication-end'])

            # Projects Chart
            elif 'project-start' in request.POST:
                request.session['project-start'] = int(request.POST['project-start'])
            elif 'project-end' in request.POST:
                request.session['project-end'] = int(request.POST['project-end'])
            
            # Map
            elif 'reset-keyword' in request.POST:
                request.session.pop('keyword-search', None)
                request.session.pop('keywords-list', None)
            elif 'keyword-search' in request.POST:
                query = request.POST['keyword-search']
                if query != '':
                    request.session['keyword-search'] = query
                    request.session['keywords-list'] = []

                    a = text_pipeline(query)
                    for keyword in Keyword.objects.all():
                        b = text_pipeline(keyword.name)
                        keyword_match = SequenceMatcher(None, a, b).ratio()
                        if (keyword_match > 0.7 or contained(a, b)) and (a != '' and b != ''):
                            #print()
                            #print(query, '____', keyword.name)
                            #print(contained(a, b), a, '____', keyword_match, '____', b,)
                            request.session['keywords-list'].append([keyword.name, True])
                else:
                    request.session.pop('keyword-search', None)
                    request.session.pop('keywords-list', None)
            elif 'keyword-update' in request.POST and 'keywords-list' in request.session:
                for keyword in request.session['keywords-list']:
                    keyword[1] = False
                for index in request.POST:
                    if index.isnumeric():
                        if int(index) >= 0 and int(index) < len(request.session['keywords-list']):
                            request.session['keywords-list'][int(index)][1] = True
            elif 'map_publication_type' in request.POST:
                request.session['map_publication_type'] = request.POST['map_publication_type']
            elif 'map_publication_start' in request.POST:
                request.session['map_publication_start'] = int(request.POST['map_publication_start'])
            elif 'map_publication_end' in request.POST:
                request.session['map_publication_end'] = int(request.POST['map_publication_end'])

        # Session initialization

        #if not 'keyword-search' in request.session:
        #    request.session['keyword-search'] = ''
        #if not 'keywords-list' in request.session:
        #    request.session['keywords-list'] = None

        # Publication types and dates

        try:
            earliest_publication = Publication.objects.earliest('date')
            latest_publication = Publication.objects.latest('date')

            # Publications Chart
            if not 'publication-type' in request.session:
                request.session['publication-type'] = "Conference Paper"
            if not 'publication-start' in request.session:
                request.session['publication-start'] = earliest_publication.date.year
            if not 'publication-end' in request.session:
                request.session['publication-end'] = latest_publication.date.year

            publication_start_range = list(reversed(range(earliest_publication.date.year, request.session['publication-end'] + 1)))
            publication_end_range = list(reversed(range(request.session['publication-start'], latest_publication.date.year + 1)))
            
            # Map
            if not 'map_publication_type' in request.session:
                request.session['map_publication_type'] = "All"
            if not 'map_publication_start' in request.session:
                request.session['map_publication_start'] = earliest_publication.date.year
            if not 'map_publication_end' in request.session:
                request.session['map_publication_end'] = latest_publication.date.year
            
            map_start_range = list(reversed(range(earliest_publication.date.year, request.session['map_publication_end'] + 1)))
            map_end_range = list(reversed(range(request.session['map_publication_start'], latest_publication.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_publication = None
            latest_publication = None

            publication_start_range = None
            publication_end_range = None

            map_start_range = None
            map_end_range = None

        
        # Projects Chart dates
        try:
            earliest_project = Project.objects.earliest('date')
            latest_project = Project.objects.latest('date')

            if not 'project-start' in request.session:
                request.session['project-start'] = earliest_project.date.year
            if not 'project-end' in request.session:
                request.session['project-end'] = latest_project.date.year
            
            project_start_range = list(reversed(range(earliest_project.date.year, request.session['project-end'] + 1)))
            project_end_range = list(reversed(range(request.session['project-start'], latest_project.date.year + 1)))

        except Publication.DoesNotExist:
            earliest_project = None
            latest_project = None
            project_start_range = None
            project_end_range = None

        # Charts
    
        labels_publications, data_publications = documents_from_year_interval(
            'Publication',
            request.session['publication-start'],
            request.session['publication-end'],
            author=pk,
            pub_type=request.session['publication-type'],
            pub_types=publication_types_options.copy()
        )
        labels_projects, data_projects = documents_from_year_interval(
            'Project',
            request.session['project-start'],
            request.session['project-end'],
            author=pk
        )

        # Top stats

        publications = Publication.objects.filter(author__id=pk).prefetch_related(
            'keywords',
            'areas',
            'author_set'
        )
        projects = Project.objects.filter(author__id=pk).prefetch_related(
            'areas'
        )

        author_keywords = {}
        author_areas = {}
        collaborators = {}

        for publication in publications:

            for keyword in publication.keywords.all():
                if not keyword.name in author_keywords:
                    author_keywords[keyword.name] = 1
                else:
                    author_keywords[keyword.name] += 1

            for area in publication.areas.all():
                if not area.name in author_areas:
                    author_areas[area.name] = [1, 0]
                else:
                    author_areas[area.name][0] += 1
            
            for author in publication.author_set.all():
                if author.pk != pk:
                    if not author.pk in collaborators:
                        collaborators[author.pk] = [1, 0]
                    else:
                        collaborators[author.pk][0] += 1
        
        for project in projects:

            for area in project.areas.all():
                if not area.name in author_areas:
                    author_areas[area.name] = [0, 1]
                else:
                    author_areas[area.name][1] += 1
            
            for author in project.author_set.all():
                if author.pk != pk:
                    if not author.pk in collaborators:
                        collaborators[author.pk] = [0, 1]
                    else:
                        collaborators[author.pk][1] += 1
        
        sorted_author_keywords = dict(sorted(author_keywords.items(), key=lambda item: item[1], reverse=True))
        sorted_author_areas = dict(sorted(author_areas.items(), key=lambda item: item[1][0] + item[1][1], reverse=True))
        sorted_collaborators = dict(sorted(collaborators.items(), key=lambda item: item[1][0] + item[1][1], reverse=True))

        # Change id to actual object
        x = {}
        for key, value in sorted_collaborators.items():
            collaborator = Author.objects.get(pk=key)
            x[collaborator] = value
        


        # Build collaboration map
        if 'keywords-list' in request.session:
            search_keywords = request.session['keywords-list']
            valid_keywords = 0
            for keyword in search_keywords:
                if keyword[1]:
                    valid_keywords += 1
        else:
            search_keywords = None
            valid_keywords = 0

        graph = author_map(
            pk = pk,
            keywords = search_keywords,
            doctype = request.session['map_publication_type'],
            start_year = request.session['map_publication_start'],
            end_year = request.session['map_publication_end'],
        )

        search_keyword = request.session['keyword-search'] if 'keyword-search' in request.session else None

        # Context build

        context = {
            'user': request.user,

            'author': this_author,
            'publications': publications,
            'projects': projects,

            'publication_types': publication_types_options,

            # Publications Chart
            'publication_type': request.session['publication-type'],
            'publication_start': request.session['publication-start'],
            'publication_end': request.session['publication-end'],
            'publication_start_range': publication_start_range,
            'publication_end_range': publication_end_range,
            
            # Projects Chart
            'project_start': request.session['project-start'],
            'project_end': request.session['project-end'],
            'project_start_range': project_start_range,
            'project_end_range': project_end_range,

            # Stats
            'sorted_author_keywords': sorted_author_keywords,
            'sorted_author_areas': sorted_author_areas,
            'sorted_collaborators': x, # sorted_collaborators but with the actual objects

            # Charts data
            'labels_publications': labels_publications,
            'data_publications': data_publications,
            'total_data_publications': sum(data_publications),

            'labels_projects': labels_projects,
            'data_projects': data_projects,
            'total_data_projects': sum(data_projects),

            # Collaboration map
            'nodes': graph['nodes'],
            'edges': graph['edges'],
            'nodes_authors': graph['nodes_authors'],
            'edges_publications': graph['edges_publications'],

            'search_keyword': search_keyword,
            'search_keywords': search_keywords,
            'valid_keywords': valid_keywords,
            'map_publication_type': request.session['map_publication_type'],

            'map_publication_start': request.session['map_publication_start'],
            'map_publication_end': request.session['map_publication_end'],
            'map_start_range': map_start_range,
            'map_end_range': map_end_range,
        }

        return render(request, 'author_detail.html', context)

    return redirect('login')

def documents_from_year_interval(doctype='Publication', start_year=date(1980, 1, 1), end_year=date.today(), author=None, pub_type='All', pub_types=[]):
    labels = []
    data = []
    cnt_year = start_year

    if 'All' in pub_types:
        pub_types.remove('All')
    if 'Other' in pub_types:
        pub_types.remove('Other')

    while(cnt_year <= end_year):
        labels.append(
            cnt_year
        )

        if doctype == 'Publication':
            publications = Publication.objects.filter(
                date__range=(
                    date(cnt_year, 1, 1),
                    date(cnt_year, 12, 31)
                )
            )

            # Author filter
            tmp_publications = publications.filter(author__id=author) if author != None else publications

            if pub_type == 'All':
                data.append( tmp_publications.count() )

            elif pub_type == 'Other':

                tmp2_publications = tmp_publications

                for i in pub_types: # Iterate important types like Conference Papers and reject them for this query (Therefore, others)
                    
                    if PublicationType.objects.filter(name=i).exists():
                        pub_type_id = PublicationType.objects.get(name=i)
                        tmp2_publications = tmp2_publications.filter(
                            ~Q(publication_type=pub_type_id)
                        )

                data.append( tmp2_publications.count() )

            else:
                try:
                    pub_type_id = PublicationType.objects.get(name=pub_type)
                    tmp2_publications = tmp_publications.filter(publication_type=pub_type_id)

                    data.append( tmp2_publications.count() )

                except PublicationType.DoesNotExist:
                    data.append( 0 )
                
                

        elif doctype == 'Project':
            projects = Project.objects.filter(
                date__range=(
                    date(cnt_year, 1, 1),
                    date(cnt_year, 12, 31)
                )
            )

            # Author filter
            tmp_projects = projects.filter(author__id=author) if author != None else projects
            data.append( tmp_projects.count() )

        cnt_year += 1

    return labels, data

def text_pipeline(text):

    # https://www.ibm.com/cloud/learn/natural-language-processing
    # https://www.analyticsvidhya.com/blog/2020/05/what-is-tokenization-nlp/

    # https://docs.python.org/3/library/difflib.html
    # https://www.nltk.org/

    # Lower case
    name = text.lower()
    # Separate words. Example: 'system-on-chip' -> 'system on chip'
    name = name.replace('-', ' ').replace('/', ' ').replace("'", ' ')
    # Tokenize
    # Won't exclude '16:9', 'systems-on-chip', 'ua.pt', ...
    tokenized = word_tokenize(name)
    # Remove non alphanumeric tokens
    new_tokanized = []
    for token in tokenized:
        if token.isalnum():
            new_tokanized.append(token)
    # Remove stop words
    stop_tokanized = []
    stop_words = set( stopwords.words('portuguese') + stopwords.words('english') )
    for token in new_tokanized:
        if not token in stop_words:
            stop_tokanized.append(token)
    return " ".join(stop_tokanized)

def contained(a, b, dbg=False):
    # check if A is in B
    contained = True
    debug(f'\na {a}', debug=dbg)
    for word in a.split(' '):
        debug(f'word {word}', debug=dbg)
        if not word in b:
            debug(f'word {word} not in {b}', debug=dbg)
            # stops when we find a word that's not in B
            contained = False
            break
    
    # only return if true
    if contained:
        return contained

    # if A is not in B, maybe B is in A
    else:
        contained = True
        debug(f'\nb {b}', debug=dbg)
        for word in b.split(' '):
            debug(f'word {word}', debug=dbg)
            if not word in a:
                debug(f'word {word} not in {a}', debug=dbg)
                contained = False
                break
        debug('', debug=dbg)
        
        return contained

def add_publication(author, scopus_id, ciencia_id, doi, title, date, \
    keywords, publication_type, from_scopus, from_ciencia, \
    available, clean_text, abstract, areas):

    debug(110*'_')
    color = bcolors.FAIL if from_scopus else bcolors.OKGREEN

    debug_text = "{}FETCH{}: [{:<11}] [{:<8}] [{:<20}] [{} {}] [{:<16}] [{} {:2d} {:2d} {} {}] [{}] \n{}".format( ############################################################################################################
        color,
        bcolors.ENDC,
        str(scopus_id)[-11:],
        str(ciencia_id)[-8:],
        str(doi)[-20:],
        bcolors.FAIL+'SC'+bcolors.ENDC if from_scopus else '  ',
        bcolors.OKGREEN+'CV'+bcolors.ENDC if from_ciencia else '  ',
        publication_type.name[-16:],
        ' ', # Authors
        len(keywords),
        len(areas),
        'Ab' if abstract != None else '  ',
        'FT' if available else '  ',
        str(date),
        title
    )
    
    merge = False
    reason = ''

    publications = Publication.objects.all()

    for test in publications.all():

        # test -> The publication that we are 'testing' against.
        # if the 'test' publication already has the info that we're trying to add,
        # we need to merge the data from both publications (onto the existing one, that being 'test').

        # Same pub. type (Yes)
        # We only want to merge publications from the same type.
        # If there's a Conference Paper and an Article about the same thing, we want to keep them
        # for counting/statistic purposes.
        if publication_type == test.publication_type:

            # Same scopus_id (Yes)
            if scopus_id != None and scopus_id == test.scopus_id:
                
                merge = True
                reason = 'same scopus'
                debug_text += f"\nTEST : { test.pretty() }"

                # Verifying that there's no different 'id info' between the 2 publications.
                # Example: They have the same 'scopus_id', but then specify different "doi"s.

                # Long code to make it understandable (only first time).

                # None and !None
                if test.ciencia_id == None and ciencia_id != None:
                    # Add new info to the test publication.
                    test.ciencia_id = ciencia_id
                # !None and None
                elif test.ciencia_id != None and ciencia_id == None:
                    # Only test publication . Do nothing.
                    pass
                # None and None
                elif test.ciencia_id == None and ciencia_id == None:
                    # Neither of them provide info. Do nothing.
                    pass
                # !None and !None
                else: # test.ciencia_id != None and ciencia_id != None:
                    if test.ciencia_id != ciencia_id:
                        # They provide different info. There may be no way to handle this merge.
                        # Same 'scopus_id' but different 'ciencia_id'
                        reason += ' different ciencia'

                        debug(debug_text)
                        debug_text = ''
                        #debug("-1-  I N C O N S I S T E N C Y  --")
                    else:
                        # They already provide the same info (!None info).
                        pass

                if test.doi == None and doi != None:
                    test.doi = doi
                elif test.doi != None and doi != None:
                    if test.doi != doi:
                        # Same 'scopus_id' but different 'doi'
                        reason += ' different doi'

                        # This is SC and test is CV -> update doi
                        if from_scopus and ( test.from_ciencia and not test.from_scopus ):
                            test.doi = doi

                        debug(debug_text)
                        debug_text = ''
                        #debug("-2-  I N C O N S I S T E N C Y  --")
                
                break
            else:

                # Same ciencia_id (Yes)
                if ciencia_id != None and ciencia_id == test.ciencia_id:

                    merge = True
                    reason = 'same ciencia'
                    debug_text += f"\nTEST : { test.pretty() }"

                    if test.scopus_id == None and scopus_id != None:
                        test.scopus_id = scopus_id
                    elif test.scopus_id != None and scopus_id != None:
                        if test.scopus_id != scopus_id:
                            # Same 'ciencia_id' but different 'scopus_id'
                            reason += ' different scopus'

                            debug(debug_text)
                            debug_text = ''
                            #debug("-3-  I N C O N S I S T E N C Y  --")

                    if test.doi == None and doi != None:
                        test.doi = doi
                    elif test.doi != None and doi != None:
                        if test.doi != doi:
                            # Same 'ciencia_id' but different 'doi'
                            reason += ' different doi'

                            debug(debug_text)
                            debug_text = ''
                            #debug("-4-  I N C O N S I S T E N C Y  --")
                    
                    break
                else:

                    # Same doi (Yes)
                    if doi != None and doi == test.doi:

                        merge = True
                        reason = 'same doi'
                        debug_text += f"\nTEST : { test.pretty() }"

                        if test.scopus_id == None and scopus_id != None:
                            test.scopus_id = scopus_id
                        elif test.scopus_id != None and scopus_id != None:
                            if test.scopus_id != scopus_id:
                                # Same 'doi' but different 'scopus_id'
                                reason += ' different scopus'

                                # This is SC and test is CV -> update SC
                                if from_scopus and ( test.from_ciencia and not test.from_scopus ):
                                    test.scopus_id = scopus_id

                                debug(debug_text)
                                debug_text = ''
                                #debug("-5-  I N C O N S I S T E N C Y  --")

                        if test.ciencia_id == None and ciencia_id != None:
                            test.ciencia_id = ciencia_id
                        elif test.ciencia_id != None and ciencia_id != None:
                            if test.ciencia_id != ciencia_id:
                                # Same 'doi' but different 'ciencia_id'
                                reason += ' different ciencia'

                                debug(debug_text)
                                debug_text = ''
                                #debug("-6-  I N C O N S I S T E N C Y  --")
                                
                        break

                    #elif False: # No title/abstract analysis (TESTING ONLY)
                    else:

                        # Title and date analysis

                        reason = ''
                        
                        if date.year == test.date.year:

                            # same abstract aka match 0.95(?)
                            if abstract != None and test.abstract != '':
                                a = text_pipeline(abstract)
                                b = text_pipeline(test.abstract)
                                abstract_match = SequenceMatcher(None, a, b).ratio()

                                if abstract_match > 0.95:
                                    merge = True
                                    reason += 'same abstract '
                            
                            abstract_count = 0
                            if abstract != None:
                                abstract_count += 1
                            if test.abstract != '':
                                abstract_count += 1

                            a = text_pipeline(title)
                            b = text_pipeline(test.title)
                            title_match = SequenceMatcher(None, a, b).ratio()
                            
                            # same title aka match 1.0
                            # 0.99 bc one doc had a typo (doing this does not increase false positives)
                            if not merge and \
                                title_match > 0.99 and \
                                abstract_count <= 1:

                                merge = True
                                reason += 'same title '
                            
                            

                            # if doc older and contains other's title
                            # like old doc (bla bla awaiting review) vs newer doc (bla bla)
                            # AND abstract only in 1 or none (because if both have an abstract
                            # and failed the first condition, then they are probably not duplicates)
                            # if (a in b or b in a) and \
                            if not merge and \
                                contained(a, b, dbg=False) and \
                                abstract_count <= 1:

                                merge = True
                                reason += 'title contained '
                        

                            if merge:

                                debug_text += f"\nTEST : { test.pretty() }"

                                debug(debug_text)
                                debug_text = ''

                                # Update scopus
                                if scopus_id != None and test.scopus_id == None:
                                    test.scopus_id = scopus_id
                                    reason += 'update scopus '
                                # Update ciencia
                                if ciencia_id != None and test.ciencia_id == None:
                                    test.ciencia_id = ciencia_id
                                    reason += 'update ciencia '
                                # Update doi
                                if doi != None and test.doi == None:
                                    test.doi = doi
                                    reason += 'update doi '

                                # Update scopus id and doi
                                if from_scopus:

                                    data_count = 0
                                    if scopus_id != None:
                                        data_count += 1
                                    if doi != None:
                                        data_count += 1
                                    if abstract != None:
                                        data_count += 1

                                    test_data_count = 0
                                    if test.scopus_id != None:
                                        test_data_count += 1
                                    if test.doi != None:
                                        test_data_count += 1
                                    if test.abstract != '':
                                        test_data_count += 1
                                    
                                    if data_count > test_data_count:
                                        if scopus_id != None:
                                            test.scopus_id = scopus_id
                                            reason += 'update scopus A '
                                        if doi != None:
                                            test.doi = doi
                                            reason += 'update doi A '
                                    else:
                                        if scopus_id != None and test.scopus_id == None:
                                            test.scopus_id = scopus_id
                                            reason += 'update scopus B '
                                        if doi != None and test.doi == None:
                                            test.doi = doi
                                            reason += 'update doi B '
                                
                                break

    if merge:

        # The 3 main fields are already taken care of
        # (scopus_id, ciencia_id, doi)

        # If new doc is more recent, update title and date
        if ( date.month == test.date.month and date.day > test.date.day ) or \
            date.month > test.date.month:

            test.title = title
            test.date = date
        elif from_scopus:

            test.title = title
            test.date = date

        if from_scopus:
            #test.title = title
            #test.date = date
            test.from_scopus = True
            if available: # Update without erasing
                test.available = available
                test.clean_text = clean_text
            if abstract != None: # Update without erasing
                test.abstract = abstract

            # Merge areas
            for area in areas:
                test.areas.add(area)

        else:
            test.from_ciencia = True

        # Merge keywords
        for keyword in keywords:
            test.keywords.add(keyword)
        
        test.save()
        author.publications.add(test)
        author.save()

        #debug_text += "\nSC {} ;; CV {} ;; DOI {} ;; {} ;; {} ;; SC {} ;; CV {} ;; AB {} ;; [{}]".format(test.scopus_id,test.ciencia_id,test.doi,test.date,test.title,test.from_scopus,test.from_ciencia,test.available,test.pk)
        
        if debug_text != '':
            debug(debug_text)
        debug(f"{ bcolors.WARNING }MERGE{ bcolors.ENDC }: { test.pretty() }")

        return reason
    
    else:

        #debug("", end=".")

        if from_scopus:
            from_scopus = True
            from_ciencia = False
            available = available
            clean_text = clean_text
            abstract = abstract
        else:
            from_scopus = False
            from_ciencia = True
            available = False
            clean_text = ""
            abstract = ""

        publication = Publication(
            scopus_id = scopus_id,
            ciencia_id = ciencia_id,
            doi = doi,
            title = title,
            date = date,
            publication_type = publication_type,

            from_scopus = from_scopus,
            from_ciencia = from_ciencia,
            available = available,
            clean_text = clean_text,
            abstract = abstract
        )
        publication.save()

        for keyword in keywords:
            publication.keywords.add(keyword)
        
        if from_scopus:

            for area in areas:
                publication.areas.add(area)
        
        publication.save()

        author.publications.add(publication)
        author.save()

        debug(f"{ color }NEW{ bcolors.ENDC }  : { publication.pretty() }")

        return 'new'

def sync_scopus_docs(pk):
    author = Author.objects.get(pk=pk)
    
    #data = scopus_author_docs(author.scopus_id)

    with open(str(author.scopus_id)+'.json', encoding="utf-8") as fh:
        data = json.load(fh)
    
    counters = {
        'new': 0,
        's_sc': 0,
            's_sc_d_cv': 0,
            's_sc_d_doi': 0,
        's_cv': 0,
            's_cv_d_sc': 0,
            's_cv_d_doi': 0,
        's_doi': 0,
            's_doi_d_sc': 0,
            's_doi_d_cv': 0,
        's_abstract': 0,
        's_title': 0,
        's_title_contained': 0,
    }

    for data_pub in data:

        # MANDATORY FIELDS
        title = data_pub['doc_title']
        if 'Erratum' in title:
            continue

        date = datetime.strptime(data_pub['doc_date'], "%Y-%m-%d").date()
        available = data_pub['available']

        # TYPE (MANDATORY)
        doc_type = data_pub['doc_type'].title()
        if doc_type == 'Erratum':
            continue
        if PublicationType.objects.filter(name=doc_type).exists():
            publication_type = PublicationType.objects.get(name=doc_type)
        else:
            publication_type = PublicationType(name=doc_type)
            publication_type.save()

        # ID'S
        scopus_id = data_pub['doc_scopus_id']
        # make doi's consistent between scopus and ciencia
        doi = data_pub['doc_doi'].lower() if data_pub['doc_doi'] != None else data_pub['doc_doi']
        doi = doi.replace('_', '-') if doi != None else doi

        # KEYWORDS
        keywords = []

        for name in data_pub['doc_keywords']:
            name = ' '.join(elem[0].upper() + elem[1:] for elem in name.split())
            name = ' '.join(elem[0].upper() + elem[1:] for elem in name.split('-'))
            # Check keyword
            if Keyword.objects.filter(name=name).exists():
                keyword = Keyword.objects.get(name=name)
            else:
                keyword = Keyword(
                    name = name
                )
                keyword.save()
            keywords.append(keyword)

        # DOCUMENT TEXT
        clean_text = data_pub['clean_text']

        abst = data_pub['doc_abstract']
        abstract = abst if abst != None else ""

        # AREAS
        areas = []

        for data_area in data_pub['doc_areas']:
            code = data_area['area_code']
            name = data_area['area_name']

            # Check area
            if Area.objects.filter(code=code).exists():
                area = Area.objects.get(code=code)
            else:
                area = Area(
                    code = code,
                    name = name
                )
                area.save()
            areas.append(area)

        reason = add_publication(
            author = author,
            scopus_id = scopus_id,
            ciencia_id = None,
            doi = doi,
            title = title,
            date = date,
            keywords = keywords,
            publication_type = publication_type,
            from_scopus = True, # SCOPUS
            from_ciencia = False,
            available = available,
            clean_text = clean_text,
            abstract = abstract,
            areas = areas
        )

        reason_F2 = " ".join( reason.split(' ')[:2] )
        reason_L2 = " ".join( reason.split(' ')[2:] )
        #print(reason, "---", reason_F2, "---", reason_L2)
        if reason == 'new':
            counters['new'] += 1
            debug(reason)
        elif reason_F2 == 'same scopus':
            counters['s_sc'] += 1
            if reason_L2 == 'different ciencia':
                counters['s_sc_d_cv'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            elif reason_L2 == 'different doi':
                counters['s_sc_d_doi'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            else:
                debug(bcolors.WARNING + reason + bcolors.ENDC)
        elif reason_F2 == 'same ciencia':
            counters['s_cv'] += 1
            if reason_L2 == 'different scopus':
                counters['s_cv_d_sc'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            elif reason_L2 == 'different doi':
                counters['s_cv_d_doi'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            else:
                debug(bcolors.WARNING + reason + bcolors.ENDC)
        elif reason_F2 == 'same doi':
            counters['s_doi'] += 1
            if reason_L2 == 'different scopus':
                counters['s_doi_d_sc'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            elif reason_L2 == 'different ciencia':
                counters['s_doi_d_cv'] += 1
                debug(bcolors.FAIL + reason + bcolors.ENDC)
            else:
                debug(bcolors.WARNING + reason + bcolors.ENDC)
        else:
            if reason_F2 == 'same abstract':
                counters['s_abstract'] += 1
            elif reason_F2 == 'same title':
                counters['s_title'] += 1
            elif reason_F2 == 'title contained':
                counters['s_title_contained'] += 1

            debug(bcolors.OKBLUE, end='')
            debug(reason)
            #debug(f'F2 {reason_F2}')
            #debug(f'L2 {reason_L2}')
            debug(bcolors.ENDC, end='')
    
    debug('')
    debug(f"new                {counters['new']}")
    debug('')
    debug(f"s_sc               {counters['s_sc']}")
    debug(f"|_ s_sc_d_cv       |_ {counters['s_sc_d_cv']}")
    debug(f"|_ s_sc_d_doi      |_ {counters['s_sc_d_doi']}")
    debug('')
    debug(f"s_cv               {counters['s_cv']}")
    debug(f"|_ s_cv_d_sc       |_ {counters['s_cv_d_sc']}")
    debug(f"|_ s_cv_d_doi      |_ {counters['s_cv_d_doi']}")
    debug('')
    debug(f"s_doi              {counters['s_doi']}")
    debug(f"|_ s_doi_d_sc      |_ {counters['s_doi_d_sc']}")
    debug(f"|_ s_doi_d_cv      |_ {counters['s_doi_d_cv']}")
    debug('')
    debug(f"s_abstract         {counters['s_abstract']}")
    debug(f"s_title            {counters['s_title']}")
    debug(f"s_title_contained  {counters['s_title_contained']}")

    return counters

def sync_scopus_author(pk):
    author = Author.objects.get(pk=pk)
    data = scopus_author(author.scopus_id)
    author.h_index = scopus_h_index(author.scopus_id)

    # DOMAINS
    for data_area in data['author_areas']:
        code = data_area['area_code']
        name = data_area['area_name']

        # Check area
        if Area.objects.filter(code=code).exists():
            area = Area.objects.get(code=code)
        else:
            area = Area(
                code = code,
                name = name
            )
            area.save()
        author.domains.add(area)

    # CITATIONS
    author.citation_count = data['author_citation_count']
    author.cited_by_count = data['author_cited_by_count']

    # CURRENT AFFILIATIONS
    for data_affiliation in data['author_current_affiliation_list']:
        affiliation_id = data_affiliation['affiliation_id']
        name = data_affiliation['affiliation_name']
        parent = data_affiliation['affiliation_parent']

        # Check affiliation
        if Affiliation.objects.filter(scopus_id=affiliation_id).exists():
            affiliation = Affiliation.objects.get(scopus_id=affiliation_id)
        else:
            affiliation = Affiliation(
                scopus_id = affiliation_id,
                name = name,
            )

        # Check parent
        if Affiliation.objects.filter(scopus_id=parent).exists():
            parent_affiliation = Affiliation.objects.get(scopus_id=parent)
            affiliation.parent = parent_affiliation
        
        affiliation.save()
        author.current_affiliations.add(affiliation)
    
    # PREVIOUS AFFILIATIONS
    for data_affiliation in data['author_previous_affiliation_list']:
        affiliation_id = data_affiliation['affiliation_id']
        name = data_affiliation['affiliation_name']
        parent = data_affiliation['affiliation_parent']

        # Check affiliation
        if Affiliation.objects.filter(scopus_id=affiliation_id).exists():
            affiliation = Affiliation.objects.get(scopus_id=affiliation_id)
        else:
            affiliation = Affiliation(
                scopus_id = affiliation_id,
                name = name,
            )

        # Check parent
        if Affiliation.objects.filter(scopus_id=parent).exists():
            parent_affiliation = Affiliation.objects.get(scopus_id=parent)
            affiliation.parent = parent_affiliation
        
        affiliation.save()
        author.previous_affiliations.add(affiliation)

    # NAMES
    # Ciência has the best names
    if author.name == "":
        author.name = data['author_name']
    author.name_list = json.dumps(data['author_name_list'])

    author.save()

def sync_ciencia(pk):
    author = Author.objects.get(pk=pk)
    #data = ciencia_author(author.ciencia_id)

    #with open(f'{author.scopus_id}_pubs_ciencia.txt', 'w', encoding="utf-8") as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    with open(str(author.scopus_id)+'_pubs_ciencia.txt', encoding="utf-8") as fh:
        data = json.load(fh)
    
    counters = {
        'new': 0,
        's_sc': 0,
            's_sc_d_cv': 0,
            's_sc_d_doi': 0,
        's_cv': 0,
            's_cv_d_sc': 0,
            's_cv_d_doi': 0,
        's_doi': 0,
            's_doi_d_sc': 0,
            's_doi_d_cv': 0,
        's_abstract': 0,
        's_title': 0,
        's_title_contained': 0,
    }

    if data != None:

        # DOMAINS
        for data_domain in data['domains']:
            code = data_domain['code']
            name = data_domain['name']

            # Check area
            if Area.objects.filter(code=code).exists():
                area = Area.objects.get(code=code)
            else:
                area = Area(
                    code = code,
                    name = name
                )
                area.save()
            author.domains.add(area)
        
        # PUBLICATIONS

        for data_publication in data['publications']:

            ciencia_id = data_publication['ciencia_id']
            scopus_id = str(data_publication['scopus_id']).split('-')[-1]
            # make doi's consistent between scopus and ciencia
            doi = data_publication['doi'].lower() if data_publication['doi'] != None else data_publication['doi']
            doi = doi.replace('_', '-') if doi != None else doi
            title = data_publication['title']
            if 'Erratum' in title:
                continue
            date = datetime.strptime(data_publication['date'], "%Y-%m-%d").date()

            # TYPE (MANDATORY)
            doc_type = data_publication['type'].title()
            if doc_type == 'Erratum' or doc_type == 'Manual':
                continue
            doc_type = 'Article' if doc_type == 'Journal Article' else doc_type
            if PublicationType.objects.filter(name=doc_type).exists():
                publication_type = PublicationType.objects.get(name=doc_type)
            else:
                publication_type = PublicationType(name=doc_type)
                publication_type.save()

            available = False

            if scopus_id == 'None':
                scopus_id = None
            
            keywords = []

            for name in data_publication['keywords']:
                # Example: a-b cd -> A-b Cd
                name = ' '.join(elem[0].upper() + elem[1:] if elem != '' else '' for elem in name.split())
                # Example: A-b Cd -> A-B Cd
                name = ' '.join(elem[0].upper() + elem[1:] if elem != '' else '' for elem in name.split('-'))
                # Check keyword
                if Keyword.objects.filter(name=name).exists():
                    keyword = Keyword.objects.get(name=name)
                else:
                    keyword = Keyword(
                        name = name
                    )
                    keyword.save()
                keywords.append(keyword)

            areas = []

            reason = add_publication(
                author = author,
                scopus_id = scopus_id,
                ciencia_id = ciencia_id,
                doi = doi,
                title = title,
                date = date,
                keywords = keywords,
                publication_type = publication_type,
                from_scopus = False,
                from_ciencia = True, # CIENCIA
                available = None,
                clean_text = None,
                abstract = None,
                areas = areas
            )

            reason_F2 = " ".join( reason.split(' ')[:2] )
            reason_L2 = " ".join( reason.split(' ')[2:] )
            #print(reason, "---", reason_F2, "---", reason_L2)
            if reason == 'new':
                counters['new'] += 1
                debug(reason)
            elif reason_F2 == 'same scopus':
                counters['s_sc'] += 1
                if reason_L2 == 'different ciencia':
                    counters['s_sc_d_cv'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                elif reason_L2 == 'different doi':
                    counters['s_sc_d_doi'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                else:
                    debug(bcolors.WARNING + reason + bcolors.ENDC)
            elif reason_F2 == 'same ciencia':
                counters['s_cv'] += 1
                if reason_L2 == 'different scopus':
                    counters['s_cv_d_sc'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                elif reason_L2 == 'different doi':
                    counters['s_cv_d_doi'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                else:
                    debug(bcolors.WARNING + reason + bcolors.ENDC)
            elif reason_F2 == 'same doi':
                counters['s_doi'] += 1
                if reason_L2 == 'different scopus':
                    counters['s_doi_d_sc'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                elif reason_L2 == 'different ciencia':
                    counters['s_doi_d_cv'] += 1
                    debug(bcolors.FAIL + reason + bcolors.ENDC)
                else:
                    debug(bcolors.WARNING + reason + bcolors.ENDC)
            else:
                if reason_F2 == 'same abstract':
                    counters['s_abstract'] += 1
                elif reason_F2 == 'same title':
                    counters['s_title'] += 1
                elif reason_F2 == 'title contained':
                    counters['s_title_contained'] += 1

                debug(bcolors.OKBLUE, end='')
                debug(reason)
                #debug(f'F2 {reason_F2}')
                #debug(f'L2 {reason_L2}')
                debug(bcolors.ENDC, end='')
        
        debug('')
        debug(f"new                {counters['new']}")
        debug('')
        debug(f"s_sc               {counters['s_sc']}")
        debug(f"|_ s_sc_d_cv       |_ {counters['s_sc_d_cv']}")
        debug(f"|_ s_sc_d_doi      |_ {counters['s_sc_d_doi']}")
        debug('')
        debug(f"s_cv               {counters['s_cv']}")
        debug(f"|_ s_cv_d_sc       |_ {counters['s_cv_d_sc']}")
        debug(f"|_ s_cv_d_doi      |_ {counters['s_cv_d_doi']}")
        debug('')
        debug(f"s_doi              {counters['s_doi']}")
        debug(f"|_ s_doi_d_sc      |_ {counters['s_doi_d_sc']}")
        debug(f"|_ s_doi_d_cv      |_ {counters['s_doi_d_cv']}")
        debug('')
        debug(f"s_abstract         {counters['s_abstract']}")
        debug(f"s_title            {counters['s_title']}")
        debug(f"s_title_contained  {counters['s_title_contained']}")

        # NAME
        # Some names come uppercased. This can uppercase wrong names but
        # still, it's better than all uppercase.
        author.name = data['name'].title()
        
        # INFO
        author.bio = data['bio']
        author.degrees = json.dumps(data['degrees'])
        author.distinctions = json.dumps(data['distinctions'])

        # PROJECTS
        for data_project in data['projects']:
            name = data_project['name']
            date = datetime.strptime(data_project['year'], "%Y").date()

            # Check project
            if Project.objects.filter(name=name).exists():
                project = Project.objects.get(name=name)
            else:
                project = Project(
                    name = name,
                    date = date
                )
                project.save()
            
            desc = data_project['desc']
            project.desc = desc if desc != None else ""

            # Project areas
            for data_area in data_project['areas']:
                code = data_area['code']
                name = data_area['name']

                # Check area
                if Area.objects.filter(code=code).exists():
                    area = Area.objects.get(code=code)
                else:
                    area = Area(
                        code = code,
                        name = name
                    )
                    area.save()
                project.areas.add(area)
            
            project.save()
            author.projects.add(project)

        author.synced_ciencia = True
        author.save()

    return counters

def debug(string='', debug=False, end="\n"):
    if debug:
        print(string, end=end)

