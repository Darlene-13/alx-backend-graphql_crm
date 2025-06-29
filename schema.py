import graphene
from crm.schema import Query as CrmQuery

class Query(CrmQuery, graphene.ObjectType):
    """
    Root Query class that combines all app-specific queries.
    """
    pass

# Create the schema
schema = graphene.Schema(query=Query)