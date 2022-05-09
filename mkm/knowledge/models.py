from django.db import models
import json

# Create your models here.

class Area(models.Model):
    code = models.IntegerField(
        primary_key = True,
    )
    name = models.CharField(
        max_length = 100
    )

    class Meta:
        ordering = ['-code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Affiliation(models.Model):
    scopus_id = models.IntegerField(
        primary_key = True
    )
    parent = models.ForeignKey(
        'Affiliation',
        on_delete = models.SET_NULL,
        null = True
    )
    name = models.CharField(
        max_length = 200
    )

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Author(models.Model):
    # NULL=TRUE IN TEXT FIELDS DOESNT MAKE SENSE

    scopus_id = models.IntegerField(
        null = True,
        blank = True
    )
    ciencia_id = models.CharField(
        max_length = 100,
        blank = True
    )
    orcid_id = models.CharField(
        max_length = 100,
        blank = True
    )

    # SCOPUS / CIENCIA
    name = models.CharField(
        max_length = 100,
        blank = True
    )
    domains = models.ManyToManyField(
        'Area',
        blank = True
    )
    publications = models.ManyToManyField(
        'Publication',
        blank = True
    )

    # SCOPUS
    name_list = models.TextField(
        default = "[]"
    )

    h_index = models.IntegerField(
        null = True,
        blank = True
    )

    citation_count = models.IntegerField(
        default = 0
    )
    cited_by_count = models.IntegerField(
        default = 0
    )

    current_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Current',
        blank = True
    )
    previous_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Previous',
        blank = True
    )

    # CIENCIA
    bio = models.TextField(
        blank = True
    )
    degrees = models.TextField(
        default = "[]"
    )
    distinctions = models.TextField(
        default = "[]"
    )
    projects = models.ManyToManyField(
        'Project',
        blank = True
    )

    # Indicates that author has been synced with Ciencia Vitae at least once
    synced_ciencia = models.BooleanField(
        default = False
    )

    class Meta:
        ordering = ['id']
        #ordering = ['name']

        unique_together = [
            ['scopus_id', 'ciencia_id', 'orcid_id'],

            # COMMENTED BECAUSE MULTIPLE AUTHORS COULD HAVE 2 FIELDS BEING NULL

            # BUT STILL NEEDS TO BE ENFORCED IN A FORM / VIEW BECAUSE THIS
            # ALLOWS FOR THE SAME ID TO EXIST IN MULTIPLE AUTHORS (BECAUSE WE
            # NEED TO ALLOW NULL)

            #['scopus_id', 'ciencia_id'],
            #['ciencia_id', 'orcid_id'],
            #['scopus_id', 'orcid_id'],
        ]
    
    def __str__(self):
        return self.name if self.name != "" else str(self.id)
    
    def load_name_list(self):
        return json.loads(self.name_list)
    
    def load_degrees(self):
        return json.loads(self.degrees)
    
    def load_distinctions(self):
        return json.loads(self.distinctions)

class Publication(models.Model):
    scopus_id = models.CharField(
        max_length = 100,
        null = True
    )
    ciencia_id = models.CharField(
        max_length = 100,
        null = True
    )
    doi = models.CharField(
        max_length = 100,
        null = True
    )

    # SCOPUS / CIENCIA
    title = models.CharField(
        max_length = 200
    )
    date = models.DateField()
    keywords = models.TextField(
        default = "[]"
    )
    publication_type = models.ForeignKey(
        'PublicationType',
        on_delete = models.CASCADE
    )

    # SCOPUS
    available = models.BooleanField()
    clean_text = models.TextField(
        blank = True
    )
    abstract = models.TextField(
        blank = True
    )
    areas = models.ManyToManyField(
        'Area'
    )

    # CIENCIA
    # No need for this! We have the reverse relation of Author-publication!
    #authors = models.ManyToManyField(
    #    'Author'
    #)

    class Meta:
        ordering = ['-date', 'title']
        unique_together = [
            ['scopus_id', 'ciencia_id']
        ]
    
    def __str__(self):
        return "[{}] {}".format( str(self.date), self.title )
    
    def load_keywords(self):
        return json.loads(self.keywords) if self.keywords != None else None

class PublicationType(models.Model):
    name = models.CharField(
        max_length = 50,
        unique = True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(
        primary_key = True,
        max_length = 200
    )
    desc = models.TextField(
        blank = True
    )
    date = models.DateField()
    areas = models.ManyToManyField(
        'Area'
    )

    class Meta:
        ordering = ['-date', 'name']

    def __str__(self):
        return "[{}] {}".format( str(self.date), self.name )
