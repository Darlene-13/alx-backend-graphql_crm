import graphene
from crm.schema import Query as CrmQuery

class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info):
        return "Hello, GraphQL!"

# Create the schema
schema = graphene.Schema(query=Query)