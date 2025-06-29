import graphene

class Query(graphene.ObjectType):
    """
    CRM app GraphQL queries.
    """
    # Define the hello field
    hello = graphene.String()

    def resolve_hello(self, info):
        """
        Resolver function for the hello field.
        This function is called when the hello field is queried
        """
        return "Hello, CRM GraphQL!"