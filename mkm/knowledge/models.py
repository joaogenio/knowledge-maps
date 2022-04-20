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
        ordering = ['name']
    
    def __str__(self):
        return self.name

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
        max_length = 100
    )

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Author(models.Model):
    scopus_id = models.IntegerField(
        null = True
    )
    ciencia_id = models.CharField(
        max_length = 100,
        null = True
    )
    orcid_id = models.CharField(
        max_length = 100,
        null = True
    )

    # SCOPUS / CIENCIA
    domains = models.ManyToManyField(
        'Area'
    )
    publications = models.ManyToManyField(
        'Publication'
    )

    # SCOPUS
    name = models.CharField(
        max_length = 100,
        null = True
    )
    name_list = models.TextField(
        null = True
    )

    citation_count = models.IntegerField(
        default = 0
    )
    cited_by_count = models.IntegerField(
        default = 0
    )

    current_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Current'
    )
    previous_affiliations = models.ManyToManyField(
        'Affiliation',
        related_name = 'Previous'
    )

    # CIENCIA
    bio = models.TextField(
        null = True
    )
    degrees = models.TextField(
        null = True
    )
    distinctions = models.TextField(
        null = True
    )
    projects = models.ManyToManyField(
        'Project'
    )

    class Meta:
        ordering = ['name']

        unique_together = [
            ['scopus_id', 'ciencia_id', 'orcid_id'],
            ['scopus_id', 'ciencia_id'],
            ['ciencia_id', 'orcid_id'],
            ['scopus_id', 'orcid_id'],
        ]
    
    def __str__(self):
        return self.name
    
    def load_name_list(self):
        return json.loads(self.name_list) if self.name_list != None else None
    
    def load_degrees(self):
        return json.loads(self.degrees) if self.degrees != None else None
    
    def load_distinctions(self):
        return json.loads(self.distinctions) if self.distinctions != None else None

class Publication(models.Model):
    scopus_id = models.IntegerField(
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
        null = True
    )
    publication_type = models.ForeignKey(
        'PublicationType',
        on_delete = models.CASCADE
    )

    # SCOPUS
    available = models.BooleanField()
    clean_text = models.TextField(
        null = True
    )
    abstract = models.TextField(
        null = True
    )
    areas = models.ManyToManyField(
        'Area'
    )

    # CIENCIA
    authors = models.ManyToManyField(
        'Author'
    )

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
        null = True
    )
    date = models.DateField()
    areas = models.ManyToManyField(
        'Area'
    )

    class Meta:
        ordering = ['-date', 'name']

    def __str__(self):
        return "[{}] {}".format( str(self.date), self.name )
